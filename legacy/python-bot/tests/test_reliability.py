import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import cv2
import numpy as np
import main_scrcpy as app
from status_store import ActionStatusStore
from workflow_result import WorkflowResult, Outcome


class ReliabilityTests(unittest.TestCase):
    def test_lower_tier_warning_is_not_a_generic_confirmation(self):
        self.assertTrue(app._is_lower_tier_training_warning("Higher-tier units unlocked. Continue training lower-tier ones?"))
        self.assertFalse(app._is_lower_tier_training_warning("Training in progress"))

    def test_shop_countdown_requires_label_and_valid_range(self):
        self.assertEqual(app._parse_shop_reset_seconds("Weekly refresh: 2d 04:03:02"), 187382)
        self.assertEqual(app._parse_shop_reset_seconds("Reset 00:01:30"), 90)
        for text in ("2d 04:03:02", "Refresh 99:99:99", "Weekly limit 3/3", "Reset 8d 00:00:00"):
            self.assertIsNone(app._parse_shop_reset_seconds(text))

    def test_cards_follow_scrolled_positions(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        for x in (220, 460, 700):
            cv2.rectangle(frame, (x-80, 1680), (x+80, 1850), (150, 40, 180), 4)
        centers = app._visible_troop_card_centers(frame, (1690,1875), (150,370,585))
        self.assertTrue(all(abs(actual-expected) < 6 for actual,expected in zip(centers,(220,460,700))))
        self.assertEqual(len(centers), 3)

    def test_blue_march_button_is_in_scoped_roi(self):
        frame = np.zeros((2160,1080,3), dtype=np.uint8)
        cv2.rectangle(frame,(340,1525),(660,1625),(220,130,40),-1)
        points = app._locate_green_rect_buttons(frame,(250,1350,750,1750),min_width=250,max_width=520,min_height=65,max_height=180,hsv_lower=(90,70,70),hsv_upper=(130,255,255))
        self.assertEqual(points, [(500,1575)])

    def test_usb_backoff_recovers_without_process_restart(self):
        bot = object.__new__(app.ScrcpyBot)
        bot.device_id = "test"
        bot.adb_logger = Mock()
        bot._invalidate_screenshot = Mock()
        disconnected = SimpleNamespace(returncode=1, stdout="")
        connected = SimpleNamespace(returncode=0, stdout="device\n")
        with patch.object(app, "_resolve_adb", return_value="adb"), patch.object(app.subprocess,"run",side_effect=[disconnected,disconnected,connected]) as run, patch.object(app.time,"monotonic",side_effect=[100,110,115,145]):
            self.assertFalse(bot._adb_transport_ready())
            self.assertFalse(bot._adb_transport_ready())
            self.assertFalse(bot._adb_transport_ready())
            self.assertTrue(bot._adb_transport_ready())
        self.assertEqual(run.call_count,3)
        self.assertEqual(run.call_args.kwargs["timeout"],3)
        self.assertEqual(bot._transport_failures,0)

    def test_usb_probe_timeout_is_a_blocked_transport(self):
        bot = object.__new__(app.ScrcpyBot)
        bot.device_id="test"
        bot.adb_logger=Mock()
        bot._invalidate_screenshot=Mock()
        with patch.object(app.subprocess,"run",side_effect=subprocess.TimeoutExpired("adb",3)):
            self.assertFalse(bot._adb_transport_ready())

    def test_results_and_schedules_survive_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"status.json"
            store=ActionStatusStore(path,{"game1":{}})
            store.record("game1","training","success","Started")
            store.record("game1","training","failed","Wrong tier")
            store.record("game1","training","failed","Wrong tier again")
            store.schedule("training_game1", 2000000000)
            loaded=ActionStatusStore(path)
            summary=loaded.account_summary("game1")["training"]
            self.assertEqual(summary["result"],"failed")
            self.assertEqual(summary["consecutive_failures"],2)
            self.assertIsNotNone(summary["last_success_at"])
            self.assertIsNotNone(summary["next_check_at"])
            self.assertEqual(loaded.scheduled_at("training_game1"),2000000000)
            loaded.record("game1","training","unavailable","Unit capacity full")
            self.assertEqual(loaded.account_summary("game1")["training"]["result"],"blocked")

    def test_normal_inactivity_is_distinct_from_failure(self):
        self.assertEqual(WorkflowResult.from_legacy("unavailable","No Hospital control").outcome,Outcome.NOTHING_TO_DO)
        self.assertEqual(WorkflowResult.from_legacy("unavailable","All marches busy").outcome,Outcome.BLOCKED)

    def test_boomer_uses_twelve_hours(self):
        self.assertEqual(app.CONFIG["boomer_auto_join"]["check_interval"],43200)

    def test_ocr_word_falls_back_to_block_segmentation(self):
        frame = np.zeros((100,200,3),dtype=np.uint8)
        empty={"text":[]}
        label={"text":["Train"],"left":[20],"top":[40],"width":[80],"height":[20]}
        with patch.object(app.pytesseract,"image_to_data",side_effect=[empty,label]) as read:
            self.assertEqual(app._find_ocr_word_center(frame,"train"),(30,25))
        self.assertIn("--psm 6", read.call_args.kwargs["config"])

    def test_failed_workflow_uses_short_retry_and_persists_it(self):
        bot = object.__new__(app.ScrcpyBot)
        bot.last_checks={}
        bot._check_intervals={"construction_game1":3600}
        bot.status_store=Mock()
        bot.status_store.account_summary.return_value={"construction":{"result":"failed"}}
        with patch.object(app.time,"time",return_value=10000):
            bot._mark_check("construction_game1")
        bot.status_store.schedule.assert_called_once_with("construction_game1",10900)

    def test_all_dynamic_helpers_survive_extraction(self):
        for name in app.HELPER_METHOD_NAMES:
            with self.subTest(name=name):
                self.assertTrue(callable(getattr(app,name)))
        self.assertEqual(app.do_build.__module__,"bot.construction")
        self.assertEqual(app.train_latest_troops.__module__,"bot.training")
        self.assertEqual(app.run_one_cycle.__module__,"bot.scheduler")

    def test_training_cancels_lower_tier_warning_instead_of_accepting(self):
        frame=np.zeros((2160,1080,3),dtype=np.uint8)
        states=[{"index":0,"center":(585,1782),"unlocked":True,"selected":True,"unlocked_score":.8},
                {"index":1,"center":(805,1782),"unlocked":False,"selected":False,"unlocked_score":0}]
        bot=SimpleNamespace(ensure_base_view=Mock(return_value=True),wait_for_template=Mock(return_value=(700,1400)),
                            adb_screenshot=Mock(return_value=frame),adb_tap=Mock(),adb_keyevent=Mock(),
                            game_logger=Mock(),_obs_capture=Mock(),_record_action=Mock(),
                            _troop_unit_cap_reached=Mock(return_value=False))
        with patch.object(app,"_troop_tier_card_states",return_value=states), \
             patch.object(app,"_find_ocr_word_center",side_effect=[None,None,(821,2065),(400,1300)]), \
             patch.object(app,"_locate_green_rect_buttons",return_value=[(821,2065)]), \
             patch.object(app,"_ocr_frame_text",return_value="Higher-tier units unlocked. Continue training lower-tier ones?"), \
             patch.object(app.time,"sleep"):
            self.assertEqual(app.train_latest_troops(bot,"game1"),"failed")
        self.assertEqual(bot.adb_tap.call_args.args,(400,1300))
        self.assertIn("lower-tier training cancelled",bot._record_action.call_args.args[3])

    def test_replenishment_confirms_inventory_then_resumes_upgrade(self):
        import bot.construction as construction
        frame=np.zeros((2160,1080,3),dtype=np.uint8)
        after=np.ones_like(frame)
        bot=SimpleNamespace(templates={},game_logger=Mock(),adb_tap=Mock(),
                            adb_screenshot=Mock(return_value=after),_obs_event=Mock(),_obs_capture=Mock())
        with patch.object(construction,"_construction_shortage_controls",return_value=(540,1720)), \
             patch.object(app,"_ocr_frame_text",side_effect=lambda image,*a,**k: "Get More Replenish All" if image is frame else "Replenish All The following resources will be used Confirm"), \
             patch.object(app,"_find_ocr_word_center",side_effect=[(700,1500),(750,1540)]), \
             patch.object(app.time,"sleep"):
            self.assertEqual(construction.handle_construction_resource_shortage(bot,frame),"replenished")
        self.assertEqual([item.args for item in bot.adb_tap.call_args_list],[(540,1720),(700,1500),(750,1540)])

    def test_insufficient_inventory_cancels_without_confirming_packs(self):
        import bot.construction as construction
        frame = np.zeros((2160,1080,3), dtype=np.uint8)
        bot = SimpleNamespace(templates={}, game_logger=Mock(), adb_tap=Mock(),
                              adb_keyevent=Mock(), adb_screenshot=Mock(return_value=frame),
                              _obs_event=Mock(), _obs_capture=Mock())
        with patch.object(construction, "_construction_shortage_controls", return_value=(540,1720)), \
             patch.object(app, "_ocr_frame_text", side_effect=["Get More Replenish All", "Using all resources still won't meet the requirements."]), \
             patch.object(app, "_find_ocr_word_center") as confirm, \
             patch.object(app.time, "sleep"):
            self.assertEqual(construction.handle_construction_resource_shortage(bot, frame), "skipped")
        bot.adb_tap.assert_called_once_with(540,1720)
        self.assertEqual([call.args for call in bot.adb_keyevent.call_args_list], [(4,), (4,)])
        confirm.assert_not_called()

    def test_healing_completion_is_not_overwritten_by_no_new_batch(self):
        from copy import deepcopy
        cfg = deepcopy(app.CONFIG["healing"])
        cfg["world_icon_wait_seconds"] = 0
        cfg["completion_templates"] = ("completion",)
        template = np.zeros((10,10,3), dtype=np.uint8)
        frame = np.zeros((2160,1080,3), dtype=np.uint8)
        bot = SimpleNamespace(templates={"completion":template}, ensure_base_view=Mock(return_value=True),
                              confirm_screen=Mock(return_value=True), game_logger=Mock(), adb_tap=Mock(),
                              adb_screenshot=Mock(return_value=frame), _record_action=Mock())
        with patch.dict(app.CONFIG, {"healing":cfg}), \
             patch.object(app, "_find_masked_template_in_roi", side_effect=lambda f,t,*a: (10,20,0) if t is template else None), \
             patch.object(app.time, "sleep"):
            self.assertTrue(app.do_heal_troops(bot, "game1"))
        self.assertEqual(bot._record_action.call_args.args[2], "success")
        self.assertIn("completion accepted", bot._record_action.call_args.args[3])
