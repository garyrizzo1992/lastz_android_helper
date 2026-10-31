import datetime as dt
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import main_scrcpy as app
from bot import shields, shield_health as health


class ShieldHealthTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root=Path(folder.name)
        self.accounts=('game1','game2','game3','game4')
        cfg=deepcopy(app.CONFIG['shield_activation'])
        cfg.update(enabled=True,ui_calibrated=True,schedule_enabled=True)
        self.patch=patch.dict(app.CONFIG,shield_state_dir=str(self.root),shield_activation=cfg)
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.bot=SimpleNamespace(game_logger=Mock(),_record_action=Mock(),launch_game=Mock(return_value=True),ensure_base_view=Mock())
        self.now=dt.datetime(2026,10,24,21,20,tzinfo=ZoneInfo('Europe/Malta'))

    def notices(self):
        return [json.loads(p.read_text()) for p in (self.root/'_health/outbox').glob('*.json')]

    def verified(self,account,hours,expiry):
        shields._save(self.root/account/f'2026-10-23-{hours}h/manifest.json',dict(state='verified',account=account,hours=hours,
            expires_at=expiry.timestamp(),remaining_seconds=expiry.timestamp()-self.now.timestamp()))

    def test_blocked_renewal_cannot_hide_in_successful_three_account_summary(self):
        for account in self.accounts:
            self.verified(account,24,self.now.replace(hour=23))
            if account!='game2':
                self.verified(account,8,self.now+dt.timedelta(hours=8))
        health.check_coverage(self.bot,self.accounts,self.now)
        health.rollout_summary(self.accounts,self.now)
        text='\n'.join(n['content'] for n in self.notices())
        self.assertIn('game2: overnight coverage is INCOMPLETE',text)
        self.assertIn('game2: NOT VERIFIED',text)
        self.assertNotIn('ALL FOUR VERIFIED',text)

    def test_uncertainty_is_not_assumed_to_prove_overnight_protection(self):
        shields._save(self.root/'game2/2026-10-23-24h/manifest.json',dict(state='uncertain',use_attempted_at=self.now.timestamp()))
        self.assertTrue(shields.shield_protection_active(self.bot,'game2'))
        self.assertFalse(health.coverage('game2')['verified'])
        health.check_coverage(self.bot,['game2'],self.now)
        self.assertIn('CANNOT BE VERIFIED',self.notices()[0]['content'])

    def test_expiry_thresholds_are_deduplicated_and_survive_restart(self):
        expiry=self.now+dt.timedelta(minutes=59)
        self.verified('game1',24,expiry)
        for minutes in (0,0,30,50,60):
            health.check_coverage(self.bot,['game1'],self.now+dt.timedelta(minutes=minutes))
        stages=[n for n in self.notices() if ':expiry:' in n['key']]
        self.assertEqual(len(stages),4)
        self.assertTrue(any(':expired' in n['key'] for n in stages))
        health.check_coverage(self.bot,['game1'],self.now+dt.timedelta(minutes=60))
        self.assertEqual(len([n for n in self.notices() if ':expiry:' in n['key']]),4)

    def test_failed_discord_delivery_persists_and_retries_without_adb(self):
        health.notice('game2:2026-10-23:unknown','URGENT game2 unknown')
        with patch.object(app,'_discord_webhook_post_many',side_effect=[OSError('offline'),True]) as post:
            health.flush(self.bot,1000)
            self.assertFalse(self.notices()[0]['delivered'])
            health.flush(self.bot,1010)
            self.assertEqual(post.call_count,1)
            health.flush(self.bot,1061)
            self.assertTrue(self.notices()[0]['delivered'])
        self.bot.launch_game.assert_not_called()

    def test_monitor_warnings_stop_after_sunday_morning(self):
        health.check_coverage(self.bot,['game2'],self.now+dt.timedelta(days=1))
        self.assertEqual(self.notices(),[])

    def test_sunday_overnight_expiry_is_not_suppressed_or_cancelled(self):
        now=dt.datetime(2026,10,25,3,30,tzinfo=self.now.tzinfo)
        expiry=now.replace(hour=4,minute=1)
        self.verified('game1',8,expiry)
        for minutes in (0, 5, 22, 32):
            at=dt.datetime.fromtimestamp(now.timestamp()+minutes*60,self.now.tzinfo)
            health.check_coverage(self.bot,['game1'],at)
        stages=[n for n in self.notices() if ':expiry:' in n['key']]
        self.assertEqual(len(stages),4)
        self.assertTrue(all('2026-10-23' in n['key'] for n in stages))
        self.assertFalse(any(n.get('cancelled') for n in stages))

    def test_monitor_window_includes_both_dst_hours(self):
        for fold in (0,1):
            local=dt.datetime(2026,10,25,2,30,tzinfo=self.now.tzinfo,fold=fold)
            self.assertTrue(health._monitoring_window(local))
        self.assertFalse(health._monitoring_window(dt.datetime(2026,10,25,6,tzinfo=self.now.tzinfo)))

    def test_sunday_live_audit_does_not_use_a_shield(self):
        import numpy as np
        ui=Mock()
        ui.timer.return_value=(np.zeros((20,20,3),dtype=np.uint8),3000)
        with patch('bot.shield_ui.BuffShieldUI',return_value=ui):
            self.assertTrue(health.audit_one(self.bot,['game1'],dt.datetime(2026,10,25,3,tzinfo=self.now.tzinfo)))
        ui.activate.assert_not_called()

    def test_coverage_target_handles_october_dst_fallback(self):
        # Saturday 21:00 + 8 elapsed hours is Sunday 04:00 after the fallback.
        expiry=dt.datetime.fromtimestamp(self.now.replace(minute=0).timestamp()+8*3600,self.now.tzinfo)
        self.assertEqual((expiry.hour,expiry.utcoffset()),(4,dt.timedelta(hours=1)))
        self.verified('game1',8,expiry)
        health.check_coverage(self.bot,['game1'],self.now)
        self.assertFalse(any('INCOMPLETE' in n['content'] for n in self.notices()))

    def test_live_audit_reads_timer_without_using_an_item(self):
        import numpy as np
        ui=Mock()
        ui.timer.return_value=(np.zeros((20,20,3),dtype=np.uint8),28000)
        with patch('bot.shield_ui.BuffShieldUI',return_value=ui):
            self.assertTrue(health.audit_one(self.bot,['game1'],self.now))
        ui.activate.assert_not_called()
        self.assertTrue(health.coverage('game1')['verified'])

    def test_newer_failed_live_check_overrides_old_success_record(self):
        self.verified('game1',8,self.now+dt.timedelta(hours=8))
        shields._save(self.root/'_health/game1.json',dict(checked_at=self.now.timestamp()+20,verified=False,reason='Timer unreadable'))
        health.rollout_summary(['game1'],self.now+dt.timedelta(minutes=1))
        self.assertFalse(health.coverage('game1')['verified'])
        self.assertTrue(any('INCOMPLETE' in n['content'] for n in self.notices()))

    def test_completed_rollout_cancels_undelivered_incomplete_summary(self):
        for account in self.accounts:
            self.verified(account,8,self.now+dt.timedelta(hours=8))
        key='summary:2026-10-23:8:False'
        health.notice(key,'Old incomplete summary')
        health.rollout_summary(self.accounts,self.now)
        old=next(n for n in self.notices() if n['key']==key)
        self.assertTrue(old['cancelled'])
        self.assertTrue(any('ALL FOUR VERIFIED' in n['content'] for n in self.notices()))

    def test_alert_screenshot_is_immutable_when_next_audit_overwrites_latest(self):
        screenshot=self.root/'_health/game1/latest.png'
        screenshot.parent.mkdir(parents=True)
        screenshot.write_bytes(b'first evidence')
        health.notice('game1:2026-10-23:unknown','Cannot verify protection')
        screenshot.write_bytes(b'newer observation')
        notice=self.notices()[0]
        self.assertEqual(Path(notice['files'][0]).read_bytes(),b'first evidence')

    def test_monitor_is_run_after_activation_window_has_closed(self):
        self.bot.do_activate_peace_shield=Mock()
        later=self.now.replace(hour=23)
        with patch.object(health,'audit_one',return_value=False) as audit, \
             patch.object(health,'check_coverage') as checks, patch.object(health,'rollout_summary'), \
             patch.object(health,'flush'):
            self.assertFalse(shields.process_scheduled_shields(self.bot,list(self.accounts),later))
        audit.assert_called_once()
        checks.assert_called_once()
        self.bot.do_activate_peace_shield.assert_not_called()

    def test_resolved_warning_can_alert_again_for_a_new_incident(self):
        key='game1:2026-10-23:unknown'
        health.notice(key,'Unknown protection')
        health.cancel(key)
        self.assertFalse(self.notices()[0]['delivered'])
        self.assertTrue(self.notices()[0]['cancelled'])
        health.notice(key,'New outage: unknown protection again')
        current=next(n for n in self.notices() if n['key']==key)
        self.assertFalse(current['delivered'])
        self.assertFalse(current.get('cancelled',False))
        with patch.object(app,'_discord_webhook_post_many',return_value=True) as post:
            health.flush(self.bot)
        self.assertIn('New outage',post.call_args.args[0])
