import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import cv2
import numpy as np
import main_scrcpy as m


class AllianceHelpTests(unittest.TestCase):
    def setUp(self):
        self.template = cv2.imread(str(m.PROJECT_ROOT / 'images/alliance_help_handshake.png'))
        self.templates = {'alliance_help_handshake': self.template}
        self.frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        h, w = self.template.shape[:2]
        self.frame[1600:1600+h, 827:827+w] = self.template
        self.empty = np.zeros_like(self.frame)

    def bot(self, screenshots):
        return SimpleNamespace(templates=self.templates, adb_tap=Mock(),
                               adb_screenshot=Mock(side_effect=screenshots),
                               game_logger=Mock(), _record_action=Mock(), _obs_capture=Mock())

    def test_current_handshake_is_detected(self):
        self.assertEqual(m._alliance_help_point(self.frame, self.templates), (867, 1634))

    def test_same_art_outside_base_shortcut_is_ignored(self):
        h, w = self.template.shape[:2]
        self.empty[800:800+h, 500:500+w] = self.template
        self.assertIsNone(m._alliance_help_point(self.empty, self.templates))

    def test_cleared_handshake_confirms_help(self):
        bot = self.bot([self.empty])
        with patch.object(m.time, 'sleep'):
            self.assertTrue(m.help_allies(bot, 'game1', self.frame))
        bot.adb_tap.assert_called_once_with(867, 1634)
        self.assertEqual(bot._record_action.call_args.args[2], 'success')

    def test_unchanged_handshake_retries_then_fails(self):
        bot = self.bot([self.frame, self.frame])
        with patch.object(m.time, 'sleep'):
            self.assertFalse(m.help_allies(bot, 'game1', self.frame))
        self.assertEqual(bot.adb_tap.call_count, 2)
        self.assertEqual(bot._record_action.call_args.args[2], 'failed')

    def test_missing_verification_frame_never_counts_as_success(self):
        bot = self.bot([None])
        with patch.object(m.time, 'sleep'):
            self.assertFalse(m.help_allies(bot, 'game1', self.frame))
        self.assertEqual(bot._record_action.call_args.args[2], 'failed')

    def test_absent_handshake_does_not_tap(self):
        bot = self.bot([])
        self.assertFalse(m.help_allies(bot, 'game1', self.empty))
        bot.adb_tap.assert_not_called()


if __name__ == '__main__':
    unittest.main()
