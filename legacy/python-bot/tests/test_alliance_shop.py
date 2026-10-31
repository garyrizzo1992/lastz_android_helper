import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import cv2
import numpy as np

import main_scrcpy
from main_scrcpy import _alliance_shop_price_button


class ShopPriceButtonTests(unittest.TestCase):
    def test_price_footer_in_same_column_not_art_or_other_card(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        for x in (70, 550):
            cv2.rectangle(frame, (x, 1780), (x + 455, 1875), (0, 190, 255), -1)
        self.assertEqual(_alliance_shop_price_button(frame, (640, 1630)), (780, 1828))

    def test_sold_out_footer_is_not_purchasable(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        cv2.rectangle(frame, (550, 1780), (1005, 1875), (150, 150, 150), -1)
        self.assertIsNone(_alliance_shop_price_button(frame, (640, 1630)))

    def test_footer_below_viewport_is_not_tapped(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        cv2.rectangle(frame, (550, 1980), (1005, 2075), (0, 190, 255), -1)
        self.assertIsNone(_alliance_shop_price_button(frame, (640, 1830)))

    def test_workflow_opens_price_footer_and_requires_reward(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        artwork = np.random.default_rng(42).integers(0, 255, (80, 80, 3), dtype=np.uint8)
        frame[1590:1670, 600:680] = artwork
        cv2.rectangle(frame, (550, 1780), (1005, 1875), (0, 190, 255), -1)
        for reward, expected in [('Congratulations! Badge', True), ('Insufficient coins', False)]:
            with self.subTest(reward=reward):
                bot = SimpleNamespace(
                    templates={'badge': artwork}, device_id='test',
                    ensure_base_view=Mock(return_value=True), adb_tap=Mock(),
                    adb_keyevent=Mock(), adb_screenshot=Mock(return_value=frame),
                    extract_text_from_roi=Mock(return_value='Badge'),
                    game_logger=Mock(), _obs_capture=Mock(), _record_action=Mock(),
                )
                with patch.dict(main_scrcpy.CONFIG['alliance_shop_badges'],
                                enabled=True, product_template='badge', product_name='badge',
                                weekly_bundle_limit=10, max_scrolls=0), \
                     patch.object(main_scrcpy.time, 'sleep'), \
                     patch.object(main_scrcpy, '_ocr_frame_text', return_value=reward):
                    self.assertEqual(main_scrcpy.do_alliance_shop_badges(bot, 'game4'), expected)
                self.assertEqual(bot.adb_tap.call_args_list[2].args, (780, 1828))
                self.assertNotIn((640, 1630), [call.args for call in bot.adb_tap.call_args_list])
                self.assertEqual(bot._record_action.call_args.args[2], 'success' if expected else 'failed')

    def test_shield_durations_are_disambiguated_and_compact_ocr_is_accepted(self):
        templates = {
            name: cv2.imread(str(main_scrcpy.PROJECT_ROOT / main_scrcpy.CONFIG['image_paths'][name]))
            for name in ('alliance_shop_peace_shield', 'alliance_shop_peace_shield_24h')
        }
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        for x, template in zip((120, 620), templates.values()):
            h, w = template.shape[:2]
            frame[1000:1000+h, x:x+w] = template
            cv2.rectangle(frame, (x-50, 1220), (x+385, 1315), (0, 190, 255), -1)
        bot = SimpleNamespace(
            templates=templates, device_id='test', ensure_base_view=Mock(return_value=True),
            adb_tap=Mock(), adb_keyevent=Mock(), adb_screenshot=Mock(return_value=frame),
            extract_text_from_roi=Mock(return_value='8hPeaceShield'),
            game_logger=Mock(), _obs_capture=Mock(), _record_action=Mock(),
        )
        with patch.dict(main_scrcpy.CONFIG['alliance_shop_badges'], enabled=True,
                        product_template='alliance_shop_peace_shield', product_name='8h peace shield',
                        weekly_bundle_limit=3, max_scrolls=0), \
             patch.object(main_scrcpy.time, 'sleep'), \
             patch.object(main_scrcpy, '_ocr_frame_text', return_value='Congratulations! 8hPeaceShield'):
            self.assertTrue(main_scrcpy.do_alliance_shop_badges(bot, 'game4'))
        self.assertEqual(bot._obs_capture.call_args_list[0].kwargs['candidates'], 1)
        self.assertLess(bot.adb_tap.call_args_list[2].args[0], 540)

    def test_exhausted_weekly_allowance_is_skipped_without_buying(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        art = np.random.default_rng(7).integers(0, 255, (80, 80, 3), dtype=np.uint8)
        frame[1590:1670, 600:680] = art
        bot = SimpleNamespace(
            templates={'badge': art}, device_id='test', ensure_base_view=Mock(return_value=True),
            adb_tap=Mock(), adb_keyevent=Mock(), adb_screenshot=Mock(return_value=frame),
            game_logger=Mock(), _obs_capture=Mock(), _record_action=Mock(),
        )
        for limit_text, footer in [('Purchase Limit:10/10', 'Sold Out This Week'),
                                   ('Purchase LimiqO/10', r'SoldjOutsihis\Week')]:
            with self.subTest(footer=footer):
                bot.adb_tap.reset_mock()
                with patch.dict(main_scrcpy.CONFIG['alliance_shop_badges'], enabled=True,
                                product_template='badge', product_name='badge', max_scrolls=0), \
                     patch.object(main_scrcpy.time, 'sleep'), \
                     patch.object(main_scrcpy, '_ocr_frame_text', side_effect=['', limit_text, footer]):
                    self.assertTrue(main_scrcpy.do_alliance_shop_badges(bot, 'game4'))
                self.assertEqual(bot.adb_tap.call_count, 2)  # navigation only
                self.assertEqual(bot._record_action.call_args.args[2], 'skipped')


if __name__ == "__main__":
    unittest.main()
