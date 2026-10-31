"""Regression checks for verified rewards rather than successful taps."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import main_scrcpy as app
from bot import daily_rewards as rewards


class DailyRewardTests(unittest.TestCase):
    def test_missing_entry_is_unavailable_not_success_or_daily_completion(self):
        with patch.object(rewards,'_open_bounties',side_effect=rewards.BountyEntryUnavailable('No visible entry')):
            self.assertFalse(rewards.do_personal_bounties(self.bot,'game1'))
        self.assertEqual(self.bot._record_action.call_args.args[2],'unavailable')
        self.bot._mark_daily_action_complete.assert_not_called()

    def test_label_fallback_must_open_verified_bounty_panel(self):
        with patch.object(rewards,'_bounty_panel',side_effect=[False,True]), \
             patch.object(rewards,'_template_center',return_value=None), \
             patch.object(app,'_find_ocr_word_center',return_value=(90,900)), \
             patch.object(rewards,'_tap',return_value='bounty panel') as tap:
            self.assertEqual(rewards._open_bounties(self.bot),'bounty panel')
        tap.assert_called_once_with(self.bot,(90,900))

    def setUp(self):
        self.bot = SimpleNamespace(ensure_base_view=Mock(return_value=True),
            _record_action=Mock(), _mark_daily_action_complete=Mock(),
            adb_tap=Mock(), adb_screenshot=Mock(return_value=object()))

    def test_vip_wrong_panel_never_claims_or_marks_daily_complete(self):
        with patch.object(rewards, '_tap', return_value=object()), patch.object(rewards, '_vip_panel', return_value=False):
            self.assertFalse(rewards.do_vip_rewards(self.bot, 'game1'))
        self.bot._mark_daily_action_complete.assert_not_called()
        self.assertEqual(self.bot._record_action.call_args.args[2], 'failed')

    def test_vip_no_reward_confirmation_does_not_mark_daily_complete(self):
        with patch.object(rewards, '_tap', return_value=object()), patch.object(rewards, '_vip_panel', return_value=True), \
                patch.object(app, '_find_ocr_word_center', return_value=(950, 515)), patch.object(rewards, '_reward_visible', return_value=False):
            self.assertFalse(rewards.do_vip_rewards(self.bot, 'game1'))
        self.bot._mark_daily_action_complete.assert_not_called()

    def test_vip_already_claimed_requires_both_cooldowns(self):
        with patch.object(rewards, '_tap', return_value=object()), patch.object(rewards, '_vip_panel', return_value=True), \
                patch.object(app, '_find_ocr_word_center', return_value=None), \
                patch.object(rewards, '_template_center', return_value=None), \
                patch.object(rewards, '_vip_cooldown', side_effect=[True,True]):
            self.assertTrue(rewards.do_vip_rewards(self.bot,'game4'))
        self.bot._mark_daily_action_complete.assert_called_once()

    def test_vip_partial_collection_retries_instead_of_completing_day(self):
        with patch.object(rewards, '_tap', return_value=object()), patch.object(rewards, '_vip_panel', return_value=True), \
                patch.object(app, '_find_ocr_word_center', return_value=None), \
                patch.object(rewards, '_template_center', return_value=None), \
                patch.object(rewards, '_vip_cooldown', side_effect=[True,False]):
            self.assertFalse(rewards.do_vip_rewards(self.bot,'game4'))
        self.bot._mark_daily_action_complete.assert_not_called()

    def test_ally_assist_requires_counter_increase(self):
        with patch.object(rewards, '_open_bounties', return_value=object()), \
                patch.object(app, '_find_ocr_word_center', return_value=(800, 690)), \
                patch.object(rewards, '_assist_counter', return_value=(0, 5)), \
                patch.object(rewards, '_bounty_button', return_value=(210, 1250)), \
                patch.object(rewards, '_tap', return_value=object()), patch.object(rewards, '_reward', return_value=object()):
            self.assertFalse(rewards.do_personal_bounties(self.bot, 'game1'))
        record = self.bot._record_action.call_args
        self.assertEqual(record.args[2], 'failed')
        self.assertEqual(record.kwargs['assisted'], 0)

    def test_template_coordinates_are_converted_to_center(self):
        import numpy as np
        bot = SimpleNamespace(find_template=Mock(return_value=(15, 20)), templates={'button':np.zeros((40, 80, 3))})
        self.assertEqual(rewards._template_center(bot, 'button', object()), (55, 40))

    def test_dispatch_success_requires_remaining_count_decrease(self):
        self.bot.templates = {'bounty_go': object()}
        for after, expected in ((1, True), (2, False)):
            self.bot._record_action.reset_mock()
            with patch.object(rewards, '_open_bounties', return_value=object()), \
                    patch.object(rewards, '_bounty_panel', return_value=True), \
                    patch.object(rewards, '_assist_counter', return_value=(5,5)), \
                    patch.object(rewards, '_bounty_button', return_value=None), \
                    patch.object(app, '_find_ocr_word_center', return_value=(800,690)), \
                    patch.object(app, '_template_match_centers', side_effect=[[(200,1200,1.0)], []]), \
                    patch.object(rewards, '_pending', side_effect=[2,after]), \
                    patch.object(rewards, '_template_center', side_effect=[(300,2060),(760,2060),None]), \
                    patch.object(rewards, '_text', return_value='conditions'), \
                    patch.object(rewards, '_tap', return_value=object()):
                self.assertEqual(rewards.do_personal_bounties(self.bot,'game1'),expected)
            self.assertEqual(self.bot._record_action.call_args.kwargs['dispatched'], int(expected))
