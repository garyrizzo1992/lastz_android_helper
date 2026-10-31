"""Shield activation is tested with simulated UI only; never consumes live items."""
from copy import deepcopy
import datetime as dt
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo
import numpy as np
import main_scrcpy as app
from bot import shields
from bot.shield_ui import ShieldUIError, BuffShieldUI, owned_count, replacement_prompt, shield_hours, shield_seconds


class ShieldParsingTests(unittest.TestCase):
    def test_durations_require_peace_shield_and_are_unambiguous(self):
        self.assertEqual(shield_hours("Peace Shield (24h)"), 24)
        self.assertEqual(shield_hours("8 hours Peace Shield"), 8)
        for text in ("24h speed up", "Peace Shield 8h or 24h", "Peace Shield 124h"):
            self.assertIsNone(shield_hours(text))

    def test_timer_requires_label_and_one_valid_countdown(self):
        self.assertEqual(shield_seconds("Peace Shield 23:59:40"), 86380)
        self.assertEqual(shield_seconds("Peace Shield 1d 00:00:00"), 86400)
        for text in ("23:59:40", "Construction 23:59:40", "Peace Shield 25:00:00",
                     "Peace Shield 00:80:00", "Peace Shield 01:00:00 02:00:00"):
            self.assertIsNone(shield_seconds(text))

    def test_inventory_count_does_not_use_selected_quantity(self):
        self.assertEqual(owned_count("Owned: 3"), 3)
        self.assertIsNone(owned_count("Use 1"))
        self.assertIsNone(owned_count("Owned 1 Quantity 2"))

    def test_replacement_confirmation_is_specific_to_selected_shield(self):
        self.assertTrue(replacement_prompt("Replace already active Peace Shield with 8h Peace Shield?", 8))
        self.assertFalse(replacement_prompt("Replace Peace Shield 24h?", 8))
        self.assertFalse(replacement_prompt("Purchase 8h Peace Shield with diamonds?", 8))
        actual = 'Tips RK\nSome Buff activated already. Further\nactivation will replace the current one.\nContinue?'
        self.assertTrue(replacement_prompt(actual,8))
        self.assertFalse(replacement_prompt(actual,3))
        self.assertFalse(replacement_prompt(actual+' Purchase with diamonds',8))

    def test_generic_replacement_requires_authorization_and_verified_controls(self):
        for replacing,allowed,target,succeeds in ((True,True,(330,1265),True),
                (False,True,(330,1265),False),(True,False,(330,1265),False),(True,True,None,False)):
            with self.subTest(replacing=replacing,allowed=allowed,target=target):
                bot=SimpleNamespace(adb_tap=Mock(),adb_keyevent=Mock())
                ui=BuffShieldUI(bot,{'confirmation_roi':(0,0,1,1),'allow_replacement':allowed,'transition_delay':0})
                ui.inventory_view,ui.frame=Mock(),Mock()
                ui.row=Mock(return_value=(17,(0,0,1,1)))
                ui.use_target=Mock(return_value=(837,1286))
                ui.text=Mock(return_value='Some Buff activated already. Further activation will replace the current one. Continue?')
                ui.replacement_confirm_target=Mock(return_value=target)
                ui.tap_text=Mock()
                if succeeds:
                    ui.activate(8,object(),replacing=replacing)
                    self.assertEqual([c.args for c in bot.adb_tap.call_args_list],[(837,1286),(330,1265)])
                    bot.adb_keyevent.assert_not_called()
                else:
                    with self.assertRaises(ShieldUIError): ui.activate(8,object(),replacing=replacing)
                    bot.adb_tap.assert_called_once_with(837,1286)
                    bot.adb_keyevent.assert_called_once_with(4)
                ui.tap_text.assert_not_called()

    def test_unknown_confirmation_is_cancelled_not_confirmed(self):
        bot = SimpleNamespace(adb_keyevent=Mock(), adb_tap=Mock())
        ui = BuffShieldUI(bot, {"confirmation_roi": (0,0,1,1)})
        ui.inventory_view = Mock()
        ui.row = Mock(return_value=(1,(0,0,1,1)))
        ui.use_target = Mock(return_value=(850,1300))
        ui.text = Mock(return_value="Confirm purchase with diamonds")
        ui.tap_text, ui.frame = Mock(), Mock()
        with self.assertRaises(ShieldUIError):
            ui.activate(24, object(), replacing=False)
        bot.adb_tap.assert_called_once_with(850,1300)
        ui.tap_text.assert_not_called()  # never generic Confirm
        bot.adb_keyevent.assert_called_once_with(4)

    def test_known_replacement_ignores_purchase_text_only_in_dimmed_background(self):
        bot=SimpleNamespace(adb_tap=Mock(),adb_keyevent=Mock())
        ui=BuffShieldUI(bot,{'confirmation_roi':(0,0,1,1),'replacement_text_roi':(1,1,2,2),
                            'allow_replacement':True,'transition_delay':0})
        ui.inventory_view,ui.frame=Mock(),Mock()
        ui.row=Mock(return_value=(17,(0,0,1,1)))
        ui.use_target=Mock(return_value=(837,1286))
        ui.text=Mock(return_value='Some Buff activated already. Purchase & Use 2000 diamonds')
        ui.replacement_confirm_target=Mock(return_value=(330,1265))
        with patch.object(app,'_ocr_frame_text',return_value='Some Buff activated already. Further activation will replace the current one. Continue?'):
            ui.activate(8,object(),replacing=True)
        self.assertEqual(bot.adb_tap.call_count,2)
        bot.adb_keyevent.assert_not_called()

    def test_last_shield_purchase_row_is_not_mistaken_for_a_confirmation(self):
        bot = SimpleNamespace(adb_keyevent=Mock(), adb_tap=Mock())
        ui = BuffShieldUI(bot, {"confirmation_roi":(0,0,1,1)})
        ui.inventory_view, ui.frame = Mock(), Mock()
        ui.row = Mock(return_value=(1,(0,0,1,1)))
        ui.use_target = Mock(return_value=(850,1300))
        ui.text = Mock(side_effect=lambda frame,name: 'Buff Info' if name=='inventory_title_roi' else 'Purchase & Use')
        ui.is_shield_panel = Mock(return_value=True)
        ui.panel_seconds = Mock(return_value=86395)
        ui.tap_text = Mock()
        ui.activate(24, object(), replacing=False)
        bot.adb_tap.assert_called_once_with(850,1300)
        bot.adb_keyevent.assert_not_called()
        ui.tap_text.assert_not_called()

    def test_existing_short_timer_does_not_bypass_unknown_confirmation(self):
        bot = SimpleNamespace(adb_keyevent=Mock(), adb_tap=Mock())
        ui = BuffShieldUI(bot, {"confirmation_roi":(0,0,1,1)})
        ui.inventory_view, ui.frame = Mock(), Mock()
        ui.row = Mock(return_value=(1,(0,0,1,1)))
        ui.use_target = Mock(return_value=(850,1300))
        ui.text = Mock(side_effect=lambda frame,name: 'Buff Info' if name=='inventory_title_roi' else 'Confirm purchase with diamonds')
        ui.is_shield_panel = Mock(return_value=True)
        ui.panel_seconds = Mock(return_value=3600)
        with self.assertRaises(ShieldUIError): ui.activate(24,object(),replacing=True)
        bot.adb_keyevent.assert_called_once_with(4)

    def test_countdown_fallback_requires_identified_shield_panel(self):
        ui = BuffShieldUI(SimpleNamespace(), {"timer_roi":(0,0,1,1),"countdown_roi":(1,1,2,2)})
        ui.text = Mock(return_value='Activated unreadable outlined header')
        ui.is_shield_panel = Mock(return_value=True)
        ui.numeric_countdown = Mock(return_value=None)
        with patch.object(app,'_ocr_frame_text',return_value='23:54:46') as ocr:
            self.assertEqual(ui.panel_seconds(object()),86086)
            ocr.assert_called_once()
        ui.is_shield_panel.return_value=False
        with patch.object(app,'_ocr_frame_text') as ocr:
            self.assertIsNone(ui.panel_seconds(object()))
            ocr.assert_not_called()

    def test_timer_retries_fresh_frames_without_any_input(self):
        ui = BuffShieldUI(SimpleNamespace(), {})
        ui.inventory_view = Mock(side_effect=['first','second'])
        ui.panel_seconds = Mock(side_effect=[None,86300])
        with patch('bot.shield_ui.time.sleep'):
            self.assertEqual(ui.timer(),('second',86300))
        self.assertEqual(ui.inventory_view.call_count,2)

    def test_outlined_digits_require_agreement_between_ocr_preparations(self):
        ui = BuffShieldUI(SimpleNamespace(), {"countdown_roi":(0,0,40,20)})
        frame=np.zeros((20,40,3),dtype=np.uint8)
        with patch('bot.shield_ui.pytesseract.image_to_string',side_effect=['23:52:52','23:52:52']):
            self.assertEqual(ui.numeric_countdown(frame),85972)
        with patch('bot.shield_ui.pytesseract.image_to_string',side_effect=['23:52:52','23:02:52']):
            self.assertIsNone(ui.numeric_countdown(frame))


    def test_purchase_background_with_transient_timer_does_not_require_title_ocr(self):
        bot=SimpleNamespace(adb_tap=Mock(),adb_keyevent=Mock())
        ui=BuffShieldUI(bot,{'confirmation_roi':(0,0,1,1)})
        ui.inventory_view=Mock()
        ui.row=Mock(return_value=(1,(0,0,1,1)))
        ui.use_target=Mock(return_value=(850,1300))
        ui.frame=Mock()
        ui.text=Mock(return_value='Purchase & Use')
        ui.is_shield_panel=Mock(return_value=True)
        ui.panel_seconds=Mock(side_effect=[None,86395])
        ui.replacement_confirm_target=Mock(return_value=None)
        with patch('bot.shield_ui.time.sleep'):
            ui.activate(24,object(),replacing=False)
        bot.adb_tap.assert_called_once_with(850,1300)
        bot.adb_keyevent.assert_not_called()
        self.assertEqual(ui.frame.call_count,2)


class ShieldWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cfg = deepcopy(app.CONFIG["shield_activation"])
        self.cfg.update(enabled=True, ui_calibrated=True, schedule_enabled=True, health_enabled=False)
        # Legacy expiry-based scheduling remains supported for existing config.
        self.cfg.update(friday_time=(22, 15), saturday_time=None)
        self.patch = patch.dict(app.CONFIG, {"debug_dir": self.temp.name, "shield_state_dir": str(Path(self.temp.name)/"shields"),
            "shield_activation": self.cfg, "discord_treasures_webhook": "https://discord.com/api/webhooks/test/test"})
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.bot = SimpleNamespace(launch_game=Mock(return_value=True), ensure_base_view=Mock(return_value=True),
                                   _record_action=Mock(), game_logger=Mock())
        self.frames = [np.full((20,10,3), value, dtype=np.uint8) for value in (40,100,180)]
        self.ui = Mock()
        self.ui.timer.side_effect = [(self.frames[0], 0), (self.frames[2], 86380)]
        self.ui.inventory.side_effect = [(self.frames[0], 2, self.frames[0]), (self.frames[1], 1, self.frames[1])]
        self.ui.inventory_view.return_value = self.frames[1]
        self.ui_factory = patch.object(shields, "BuffShieldUI", return_value=self.ui).start()
        self.addCleanup(patch.stopall)
        self.post = patch.object(app, "_discord_webhook_post_many", return_value=True).start()
        self.key = "2026-10-16-24h"

    def manifest(self):
        return Path(self.temp.name) / "shields/game1" / self.key / "manifest.json"

    def run_activation(self):
        return shields.do_activate_peace_shield(self.bot, "game1", 24, self.key)

    def test_default_disabled_and_uncalibrated_have_zero_side_effects(self):
        for enabled, calibrated in ((False,False), (True,False), (False,True)):
            self.cfg.update(enabled=enabled, ui_calibrated=calibrated)
            self.assertFalse(self.run_activation())
        self.bot.launch_game.assert_not_called()
        self.ui_factory.assert_not_called()
        self.post.assert_not_called()
        self.assertFalse(self.manifest().exists())

    def test_all_three_screenshots_and_durable_fence_precede_success(self):
        def check_fence(*args, **kwargs):
            saved = json.loads(self.manifest().read_text())
            self.assertEqual(saved["state"], "activation_attempted")
            self.assertIn("before", saved["screenshots"])
        self.ui.activate.side_effect = check_fence
        self.assertTrue(self.run_activation())
        saved = json.loads(self.manifest().read_text())
        self.assertEqual(saved["state"], "verified")
        self.assertEqual(saved["before_count"], 2)
        self.assertEqual(saved["after_count"], 1)
        self.assertTrue(saved["discord_delivered"])
        files = self.post.call_args.args[2]
        self.assertEqual([row[0] for row in files], [row[1] for row in shields.STAGES])
        self.assertIn("game1", self.post.call_args.args[0])
        self.assertIn("Europe/Malta", self.post.call_args.args[0])

    def test_report_retry_does_not_use_another_shield(self):
        self.post.side_effect = [False, True]
        self.assertTrue(self.run_activation())
        self.assertFalse(json.loads(self.manifest().read_text())["discord_delivered"])
        self.assertTrue(self.run_activation())
        self.ui.activate.assert_called_once()
        self.assertTrue(json.loads(self.manifest().read_text())["discord_delivered"])

    def test_wrong_timer_marks_uncertain_and_fences_repeated_use(self):
        self.ui.timer.side_effect = [(self.frames[0], 0), (self.frames[2], 500)]
        self.assertFalse(self.run_activation())
        self.assertEqual(json.loads(self.manifest().read_text())["state"], "uncertain")
        self.assertFalse(self.run_activation())
        self.ui.activate.assert_called_once()
        self.assertTrue(shields.shield_protection_active(self.bot, "game1"))

    def test_wrong_inventory_delta_cannot_report_success(self):
        self.ui.inventory.side_effect = [(self.frames[0],2,self.frames[0]), (self.frames[1],2,self.frames[1])]
        self.assertFalse(self.run_activation())
        self.assertEqual(json.loads(self.manifest().read_text())["state"], "uncertain")
        self.assertIn("NOT VERIFIED", self.post.call_args.args[0])

    def test_unreadable_last_stack_is_not_claimed_as_full_verification(self):
        self.ui.inventory.side_effect = [(self.frames[0],1,self.frames[0]), ShieldUIError("stack absent")]
        self.assertFalse(self.run_activation())
        saved = json.loads(self.manifest().read_text())
        self.assertEqual(saved["state"], "uncertain")
        self.assertIn("inventory proof needs review", self.post.call_args.args[0])

    def test_owned_zero_after_using_final_shield_is_verified(self):
        self.ui.inventory.side_effect = [(self.frames[0],1,self.frames[0]), (self.frames[1],0,self.frames[1])]
        self.assertTrue(self.run_activation())
        self.assertEqual(json.loads(self.manifest().read_text())["after_count"], 0)

    def test_unknown_confirmation_recovers_without_second_use(self):
        self.ui.activate.side_effect=ShieldUIError('Unknown confirmation was cancelled; manual review required')
        self.ui.timer.side_effect=[(self.frames[0],0),(self.frames[2],86398),(self.frames[2],86397)]
        self.assertTrue(self.run_activation())
        self.ui.activate.assert_called_once()
        saved=json.loads(self.manifest().read_text())
        self.assertEqual(saved['state'],'verified')
        self.assertTrue(saved['inventory_delta_verified'])
        self.assertIn('after',saved['screenshots'])
        self.assertIn('timer',saved['screenshots'])

    def test_unknown_attempt_recovery_cannot_consume_again_after_restart(self):
        import time
        shields._save(self.manifest(),dict(account='game1',hours=24,operation=self.key,state='uncertain',
            before_count=1,use_attempted_at=time.time()-100,started_at=time.time()-100,screenshots={}))
        self.ui.timer.side_effect=[(self.frames[2],86299)]
        self.ui.inventory.side_effect=[(self.frames[1],1,self.frames[1])]
        self.assertFalse(self.run_activation())
        self.ui.activate.assert_not_called()
        self.assertEqual(shields._read(self.manifest())['state'],'uncertain')

    def test_persisted_uncertain_attempt_is_reconciled_by_fresh_proof(self):
        import time
        shields._save(self.manifest(),dict(account='game1',hours=24,operation=self.key,state='uncertain',
            before_count=1,use_attempted_at=time.time()-100,started_at=time.time()-100,screenshots={}))
        self.ui.timer.side_effect=[(self.frames[2],86299),(self.frames[2],86298)]
        self.ui.inventory.side_effect=[(self.frames[1],0,self.frames[1])]
        self.assertTrue(self.run_activation())
        self.ui.activate.assert_not_called()
        self.assertTrue(self.manifest().with_name('manifest.before-reconciliation.json').exists())

    def test_old_uncertainty_blocks_new_operation_and_queues_alert(self):
        import time
        from bot import shield_health
        old=self.manifest().parent.parent/'2026-10-09-24h/manifest.json'
        shields._save(old,dict(account='game1',hours=24,operation='2026-10-09-24h',state='uncertain',
            before_count=1,use_attempted_at=time.time()-100,started_at=time.time()-100,screenshots={}))
        self.ui.inventory.side_effect=[(self.frames[1],1,self.frames[1])]
        self.assertFalse(self.run_activation())
        self.ui.activate.assert_not_called()
        saved=json.loads(self.manifest().read_text())
        self.assertEqual(saved['state'],'blocked')
        self.assertIn('Unreconciled',saved['reason'])
        shield_health.flush(self.bot)
        self.assertIn('BLOCKED',self.post.call_args.args[0])

    def test_expired_uncertainty_is_archived_without_repeating_use(self):
        import time
        shields._save(self.manifest(),dict(account='game1',hours=24,operation=self.key,state='uncertain',
            before_count=1,use_attempted_at=time.time()-90000,started_at=time.time()-90000,screenshots={}))
        self.ui.timer.side_effect=[(self.frames[2],4000)]
        self.ui.inventory.side_effect=[(self.frames[1],3,self.frames[1])]
        self.assertFalse(self.run_activation())
        self.assertEqual(shields._read(self.manifest())['state'],'expired_unverified')
        self.ui.activate.assert_not_called()

    def test_concurrent_or_stale_activation_lock_prevents_use(self):
        self.manifest().parent.parent.mkdir(parents=True)
        (self.manifest().parent.parent / "activation.lock").touch()
        self.assertFalse(self.run_activation())
        self.ui.activate.assert_not_called()

    def test_missing_webhook_blocks_before_touching_phone(self):
        with patch.dict(app.CONFIG, {"discord_treasures_webhook":"", "discord_webhook":"https://discord.com/api/webhooks/wrong/channel"}), \
             patch.dict(shields.os.environ, {"DISCORD_TREASURES_WEBHOOK_URL":""}):
            self.assertFalse(self.run_activation())
        self.bot.launch_game.assert_not_called()
        self.ui.activate.assert_not_called()

    def test_existing_longer_protection_never_consumes_another_item(self):
        self.ui.timer.side_effect = [(self.frames[0], 86360), (self.frames[2], 86340)]
        self.assertTrue(self.run_activation())
        self.ui.activate.assert_not_called()
        self.assertEqual(json.loads(self.manifest().read_text())["state"], "already_protected")

    def test_replacement_with_substantial_time_remaining_is_blocked(self):
        self.ui.timer.side_effect = [(self.frames[0], 4*3600)]
        self.assertFalse(shields.do_activate_peace_shield(self.bot,"game1",8,"2026-10-16-8h"))
        self.ui.activate.assert_not_called()

    def test_friday_24h_can_extend_an_existing_shorter_shield(self):
        self.ui.timer.side_effect = [(self.frames[0], 4*3600), (self.frames[2],86380)]
        self.assertTrue(self.run_activation())
        self.assertTrue(self.ui.activate.call_args.kwargs["replacing"])

    def test_corrupted_manifest_never_causes_new_use(self):
        self.manifest().parent.mkdir(parents=True)
        self.manifest().write_text("bad json")
        with self.assertRaises(json.JSONDecodeError):
            self.run_activation()
        self.ui.activate.assert_not_called()

    def test_friday_schedule_uses_malta_time_in_summer_and_winter(self):
        for day, utc_hour in ((16,20), (30,21)):
            now = dt.datetime(2026,10,day,utc_hour,15,tzinfo=dt.timezone.utc)
            self.assertEqual(shields.shield_operations(now, self.cfg, "game1"), (24,f"2026-10-{day}-24h"))
            self.assertIsNone(shields.shield_operations(now - dt.timedelta(minutes=1), self.cfg, "game1"))

    def test_weekly_fixed_times_recur_and_follow_malta_dst(self):
        self.cfg.update(friday_time=(23, 0), saturday_time=(21, 0))
        for day, utc_hour in ((16, 21), (23, 21), (30, 22)):
            friday = dt.datetime(2026,10,day,utc_hour,tzinfo=dt.timezone.utc)
            saturday = friday + dt.timedelta(hours=22)
            for account in self.cfg['accounts']:
                self.assertIsNone(shields.shield_operations(friday-dt.timedelta(seconds=1),self.cfg,account))
                self.assertEqual(shields.shield_operations(friday,self.cfg,account),(24,f'2026-10-{day}-24h'))
                self.assertIsNone(shields.shield_operations(saturday-dt.timedelta(seconds=1),self.cfg,account))
                self.assertEqual(shields.shield_operations(saturday,self.cfg,account),(8,f'2026-10-{day}-8h'))
                self.assertIsNone(shields.shield_operations(saturday+dt.timedelta(hours=1,seconds=1),self.cfg,account))
            self.assertEqual(shields.shield_start_delay(self.cfg,saturday-dt.timedelta(minutes=5)),300)

    def test_fixed_saturday_extends_two_hours_without_prior_friday_manifest(self):
        self.cfg['saturday_time'] = (21, 0)
        self.ui.timer.side_effect = [(self.frames[0],7200),(self.frames[2],28798)]
        self.assertTrue(shields.do_activate_peace_shield(self.bot,'game1',8,'2026-10-16-8h'))
        self.ui.activate.assert_called_once()
        self.assertTrue(self.ui.activate.call_args.kwargs['replacing'])

    def test_saturday_renewal_follows_each_accounts_verified_expiry(self):
        expiry = dt.datetime(2026,10,17,22,25,tzinfo=ZoneInfo("Europe/Malta")).timestamp()
        shields._save(self.manifest(), {"state":"verified", "expires_at":expiry})
        now = dt.datetime(2026,10,17,21,55,tzinfo=ZoneInfo("Europe/Malta"))
        self.assertEqual(shields.shield_operations(now,self.cfg,"game1"),(8,"2026-10-16-8h"))
        self.assertIsNone(shields.shield_operations(now - dt.timedelta(minutes=1),self.cfg,"game1"))

    def test_dated_start_waits_until_due_and_does_not_recur_next_week(self):
        self.cfg["one_off_start_at"] = "2026-10-16T23:30:00+02:00"
        start = dt.datetime.fromisoformat(self.cfg["one_off_start_at"])
        self.assertIsNone(shields.shield_operations(start-dt.timedelta(seconds=1),self.cfg,"game1"))
        self.assertEqual(shields.shield_operations(start,self.cfg,"game1"),(24,self.key))
        self.assertIsNone(shields.shield_operations(start+dt.timedelta(hours=1,seconds=1),self.cfg,"game1"))
        self.assertIsNone(shields.shield_operations(start+dt.timedelta(days=7),self.cfg,"game1"))

    def test_dated_start_requires_timezone_and_pre_reset_window(self):
        now=dt.datetime(2026,10,16,23,0,tzinfo=ZoneInfo("Europe/Malta"))
        for value in ("2026-10-16T23:30:00", "2026-10-17T04:00:00+02:00", "invalid"):
            self.cfg["one_off_start_at"] = value
            with self.assertRaises(ValueError): shields.shield_operations(now,self.cfg,"game1")

    def test_dated_start_preserves_saturday_renewal(self):
        self.cfg["one_off_start_at"] = "2026-10-16T23:30:00+02:00"
        expiry=dt.datetime(2026,10,17,23,30,tzinfo=ZoneInfo("Europe/Malta"))
        shields._save(self.manifest(), {"state":"verified", "expires_at":expiry.timestamp()})
        self.assertEqual(shields.shield_operations(expiry-dt.timedelta(minutes=30),self.cfg,"game1"),(8,"2026-10-16-8h"))

    def test_explicit_8h_rollout_targets_all_accounts(self):
        self.cfg.update(one_off_8h_start_at='2026-10-17T23:40:00+02:00',
                        rollout_8h_accounts=('game1','game2','game3','game4'))
        start=dt.datetime.fromisoformat(self.cfg['one_off_8h_start_at'])
        self.assertIsNone(shields.shield_operations(start-dt.timedelta(seconds=1),self.cfg,'game3'))
        self.assertEqual(shields.shield_operations(start,self.cfg,'game3'),(8,'2026-10-16-8h'))
        self.assertEqual(shields.shield_operations(start+dt.timedelta(hours=1),self.cfg,'game4'),(8,'2026-10-16-8h'))
        self.assertIsNone(shields.shield_operations(start+dt.timedelta(hours=1,seconds=1),self.cfg,'game1'))

    def test_excluded_24h_account_still_receives_saturday_8h_renewal(self):
        self.cfg.update(one_off_start_at='2026-10-16T23:55:00+02:00',rollout_accounts=('game3','game4'))
        start=dt.datetime.fromisoformat(self.cfg['one_off_start_at'])
        self.assertIsNone(shields.shield_operations(start,self.cfg,'game1'))
        self.assertIsNone(shields.shield_operations(start,self.cfg,'game2'))
        self.assertEqual(shields.shield_operations(start,self.cfg,'game3'),(24,self.key))
        self.assertEqual(shields.shield_operations(start,self.cfg,'game4'),(24,self.key))
        expiry=dt.datetime(2026,10,17,23,31,tzinfo=ZoneInfo('Europe/Malta'))
        shields._save(self.manifest(),{'state':'verified','expires_at':expiry.timestamp()})
        self.assertEqual(shields.shield_operations(expiry-dt.timedelta(minutes=30),self.cfg,'game1'),(8,'2026-10-16-8h'))

    def test_near_term_rollout_holds_normal_rotation_only_when_armed(self):
        self.cfg["one_off_start_at"] = "2026-10-16T23:30:00+02:00"
        start = dt.datetime.fromisoformat(self.cfg["one_off_start_at"])
        self.assertEqual(shields.shield_start_delay(self.cfg,start-dt.timedelta(minutes=5)),300)
        self.assertEqual(shields.shield_start_delay(self.cfg,start-dt.timedelta(hours=1)),0)
        self.assertEqual(shields.shield_start_delay(self.cfg,start),0)
        for gate in ("enabled", "ui_calibrated", "schedule_enabled"):
            with patch.dict(self.cfg,{gate:False}):
                self.assertEqual(shields.shield_start_delay(self.cfg,start-dt.timedelta(minutes=5)),0)

    def test_priority_sweep_targets_all_four_accounts(self):
        self.bot.do_activate_peace_shield = Mock(return_value=True)
        now = dt.datetime(2026,10,16,22,15,tzinfo=ZoneInfo("Europe/Malta"))
        self.assertTrue(shields.process_scheduled_shields(self.bot, ["game1","game2","game3","game4","game5"], now))
        self.assertEqual([call.args[0] for call in self.bot.do_activate_peace_shield.call_args_list],
                         ["game1","game2","game3","game4"])

    def test_priority_sweep_never_activates_excluded_rollout_accounts(self):
        self.cfg.update(one_off_start_at='2026-10-16T23:55:00+02:00',rollout_accounts=('game3','game4'))
        self.bot.do_activate_peace_shield=Mock(return_value=True)
        now=dt.datetime.fromisoformat(self.cfg['one_off_start_at'])
        self.assertTrue(shields.process_scheduled_shields(self.bot,['game1','game2','game3','game4'],now))
        self.assertEqual([c.args[0] for c in self.bot.do_activate_peace_shield.call_args_list],['game3','game4'])

    def test_schedule_needs_separate_approval(self):
        for gate in ("enabled", "ui_calibrated", "schedule_enabled"):
            with patch.dict(self.cfg, {gate:False}):
                self.assertFalse(shields.process_scheduled_shields(self.bot,["game1"]))
        self.bot.launch_game.assert_not_called()
        self.post.assert_not_called()

    def test_late_friday_catchup_can_renew_before_sunday_expiry(self):
        expiry = dt.datetime(2026,10,18,2,0,tzinfo=ZoneInfo("Europe/Malta")).timestamp()
        shields._save(self.manifest(), {"state":"verified", "expires_at":expiry})
        now = dt.datetime(2026,10,18,1,30,tzinfo=ZoneInfo("Europe/Malta"))
        self.assertEqual(shields.shield_operations(now,self.cfg,"game1"),(8,"2026-10-16-8h"))


class DiscordShieldEvidenceTests(unittest.TestCase):
    def test_ordered_multipart_payload_waits_for_discord_acknowledgement(self):
        files = [(name,b"PNG",caption) for _,name,caption in shields.STAGES]
        response = io.BytesIO(json.dumps({"id":"message", "attachments":[{"filename":name} for name, _, _ in files]}).encode())
        with patch("bot.observability.urllib.request.urlopen", return_value=response) as post:
            self.assertTrue(app._discord_webhook_post_many("account evidence", "https://discord.com/api/webhooks/a/b", files))
        request = post.call_args.args[0]
        self.assertIn("wait=true", request.full_url)
        self.assertIn(b'"allowed_mentions": {"parse": []}', request.data)
        for index in range(3):
            self.assertIn(f'files[{index}]'.encode(), request.data)

    def test_unacknowledged_upload_is_not_reported_delivered(self):
        with patch("bot.observability.urllib.request.urlopen", return_value=io.BytesIO(b"{}")):
            self.assertFalse(app._discord_webhook_post_many("evidence", "https://discord.com/api/webhooks/a/b", []))

    def test_images_returned_only_as_embeds_are_acknowledged(self):
        files = [(name,b"PNG",caption) for _,name,caption in shields.STAGES]
        message = {"id":"message", "attachments":[], "embeds":[
            {"image":{"url":"https://cdn.discordapp.com/attachments/channel/item/" + name + "?signed=1",
                      "width":1080, "height":2160}} for name, _, _ in files]}
        with patch("bot.observability.urllib.request.urlopen", return_value=io.BytesIO(json.dumps(message).encode())):
            self.assertTrue(app._discord_webhook_post_many("evidence", "https://discord.com/api/webhooks/a/b", files))

    def test_partial_or_untrusted_embed_images_are_not_acknowledged(self):
        files = [("before.png",b"PNG","before"),("after.png",b"PNG","after")]
        image = {"url":"https://cdn.discordapp.com/attachments/channel/item/before.png", "width":1080,"height":2160}
        for images in ([image], [image,dict(image)],
                       [image,{**image,"url":"https://example.com/after.png"}],
                       [image,{**image,"url":"https://cdn.discordapp.com/after.png","width":0}]):
            message = {"id":"message","attachments":[],"embeds":[{"image":i} for i in images]}
            with patch("bot.observability.urllib.request.urlopen", return_value=io.BytesIO(json.dumps(message).encode())):
                self.assertFalse(app._discord_webhook_post_many("evidence", "https://discord.com/api/webhooks/a/b", files))

    def test_unsafe_filename_or_wrong_host_is_rejected_without_network(self):
        with patch("bot.observability.urllib.request.urlopen") as post:
            self.assertFalse(app._discord_webhook_post_many("evidence", "https://discord.com/api/webhooks/a/b", [('bad\r\n.png',b'PNG','x')]))
            self.assertFalse(app._discord_webhook_post_many("evidence", "https://example.com/api/webhooks/a/b", []))
            post.assert_not_called()
