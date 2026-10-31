import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import cv2
import numpy as np
import main_scrcpy

from main_scrcpy import (
    _locate_available_builder_button,
    _locate_boomer_event_card,
    _locate_boomer_activate_button,
    _locate_builder_help_pin,
    _locate_green_builder_upgrade,
    _locate_green_rect_buttons,
    _is_construction_resource_shortage_prompt,
    _is_construction_replenish_confirmation,
    _is_boomer_auto_join_enabled,
    _ocr_title_matches,
    _parse_attempts_fraction,
)


class BuilderDetectionTests(unittest.TestCase):
    def test_locates_free_builder_in_first_row(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        template = cv2.imread("images/builder_build.png", cv2.IMREAD_UNCHANGED)
        top, left = 680, 650
        frame[top:top + template.shape[0], left:left + template.shape[1]] = template[:, :, :3]
        match = _locate_available_builder_button(frame, template)
        self.assertIsNotNone(match)
        self.assertEqual(match[:2], (left + template.shape[1] // 2, top + 95))

    def test_multiple_free_builders_remain_detectable_as_each_row_becomes_busy(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        template = cv2.imread("images/builder_build.png", cv2.IMREAD_UNCHANGED)
        height, width = template.shape[:2]
        for top in (700, 925, 1150, 1375):
            frame[top:top+height, 650:650+width] = template[:, :, :3]
        remaining = {top + 95 for top in (700, 925, 1150, 1375)}
        while remaining:
            match = _locate_available_builder_button(frame, template)
            self.assertIsNotNone(match)
            self.assertIn(match[1], remaining)
            remaining.remove(match[1])
            top = match[1] - 95
            # Replace the entire served row with an occupied blue control.
            frame[top:top+height, 650:650+width] = (220, 130, 40)
        self.assertIsNone(_locate_available_builder_button(frame, template))

    def test_builder_queue_opening_retries_without_claiming_workers_busy(self):
        bot = SimpleNamespace(
            adb_screenshot=Mock(side_effect=["base", "base", "base", "queue"]),
            templates={"builder_hardhat": object()}, adb_tap=Mock(),
            game_logger=Mock(), _obs_capture=Mock(), _record_action=Mock(),
        )
        with patch.object(main_scrcpy, '_builder_queue_is_open', side_effect=lambda f, t: f == 'queue'), \
             patch.object(main_scrcpy, '_template_match_centers', return_value=[(66, 391, 1.0)]), \
             patch.object(main_scrcpy.time, 'monotonic', side_effect=[0, 0, 4, 10, 10]), \
             patch.object(main_scrcpy.time, 'sleep'):
            self.assertEqual(main_scrcpy.open_builder_queue(bot, 'game1'), 'queue')
        self.assertEqual(bot.adb_tap.call_count, 2)
        bot._record_action.assert_not_called()

    def test_failed_menu_open_is_a_navigation_failure(self):
        bot = SimpleNamespace(
            adb_screenshot=Mock(return_value='base'), templates={'builder_hardhat': object()},
            adb_tap=Mock(), game_logger=Mock(), _obs_capture=Mock(), _record_action=Mock(),
        )
        with patch.object(main_scrcpy, '_builder_queue_is_open', return_value=False), \
             patch.object(main_scrcpy, '_template_match_centers', return_value=[(66, 391, 1.0)]), \
             patch.object(main_scrcpy.time, 'monotonic', side_effect=[0, 4]), \
             patch.dict(main_scrcpy.CONFIG['builder_navigation'], max_attempts=1):
            self.assertIsNone(main_scrcpy.open_builder_queue(bot, 'game1'))
        self.assertEqual(bot._record_action.call_args.args[1:3], ('construction_navigation', 'failed'))

    def test_locates_available_builder_after_occupied_first_row(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        template = cv2.imread("images/builder_build.png", cv2.IMREAD_UNCHANGED)
        self.assertIsNotNone(template)
        # The first row is occupied and contains blue Speed Up.  The first
        # genuine Build control is on the next available-worker row.
        top, left = 920, 650
        frame[top:top + template.shape[0], left:left + template.shape[1]] = template[:, :, :3]

        match = _locate_available_builder_button(frame, template)

        self.assertIsNotNone(match)
        self.assertEqual(match[:2], (left + template.shape[1] // 2, top + 95))

    def test_locates_danger_lurks_by_boomer_portrait(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        template = cv2.imread("images/archive/boomer.png", cv2.IMREAD_UNCHANGED)
        self.assertIsNotNone(template)
        scaled = cv2.resize(template[:, :, :3], None, fx=0.75, fy=0.75, interpolation=cv2.INTER_AREA)
        top, left = 2010, 780
        frame[top:top + scaled.shape[0], left:left + scaled.shape[1]] = scaled

        match = _locate_boomer_event_card(frame, template)

        self.assertIsNotNone(match)
        self.assertEqual(
            match[:2],
            (left + scaled.shape[1] // 2, top + scaled.shape[0] // 2),
        )

    def test_locates_boomer_activate_button_without_ocr(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        cv2.rectangle(frame, (553, 1658), (950, 1781), (20, 180, 245), thickness=-1)

        point = _locate_boomer_activate_button(frame)

        self.assertIsNotNone(point)
        self.assertLessEqual(abs(point[0] - 751), 2)
        self.assertLessEqual(abs(point[1] - 1719), 2)

    def test_locates_green_builder_upgrade_with_white_arrow(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        cv2.circle(frame, (625, 1315), 55, (45, 175, 80), thickness=-1)
        arrow = np.array(
            [[625, 1275], [595, 1310], [613, 1310], [613, 1350],
             [637, 1350], [637, 1310], [655, 1310]],
            dtype=np.int32,
        )
        cv2.fillPoly(frame, [arrow], (245, 245, 245))

        point = _locate_green_builder_upgrade(frame)

        self.assertIsNotNone(point)
        self.assertLessEqual(abs(point[0] - 625), 5)
        self.assertLessEqual(abs(point[1] - 1315), 5)

    def test_rejects_green_control_without_white_upgrade_arrow(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        cv2.circle(frame, (625, 1315), 55, (45, 175, 80), thickness=-1)

        self.assertIsNone(_locate_green_builder_upgrade(frame))

    def test_locates_builder_help_pin_in_recentered_building_area(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        cv2.circle(frame, (540, 815), 50, (215, 220, 215), thickness=-1)
        cv2.rectangle(frame, (505, 800), (575, 830), (25, 25, 25), thickness=-1)

        point = _locate_builder_help_pin(frame)

        self.assertIsNotNone(point)
        self.assertLessEqual(abs(point[0] - 540), 5)
        self.assertLessEqual(abs(point[1] - 815), 10)

    def test_locates_green_claim_button_in_scoped_roi(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        cv2.rectangle(frame, (760, 950), (978, 1040), (65, 180, 95), thickness=-1)

        buttons = _locate_green_rect_buttons(
            frame,
            (700, 850, 1020, 1900),
            min_width=170,
            max_width=260,
        )

        self.assertEqual(buttons, [(869, 995)])

    def test_alliance_gifts_title_tolerates_observed_ocr_error(self):
        self.assertTrue(_ocr_title_matches("AilianceGiftsy", "Alliance Gifts"))
        self.assertTrue(_ocr_title_matches("Allianee5", "Alliance"))
        self.assertFalse(_ocr_title_matches("Alliance Techs", "Alliance Gifts"))

    def test_attempts_fraction_repairs_merged_leading_digit(self):
        self.assertEqual(_parse_attempts_fraction("Counter: 116/20"), (16, 20))
        self.assertEqual(_parse_attempts_fraction("Counter: 0/20"), (0, 20))

    def test_construction_shortage_requires_the_specific_prompt(self):
        self.assertTrue(_is_construction_resource_shortage_prompt(
            "Insufficient Resources\nReplenish All\nSkip Construction"
        ))
        self.assertFalse(_is_construction_resource_shortage_prompt(
            "Replenish inventory resources"
        ))
        self.assertFalse(_is_construction_resource_shortage_prompt(
            "Insufficient troop capacity\nSkip"
        ))
        self.assertTrue(_is_construction_resource_shortage_prompt(
            "Get More\n1,000 Wood\nReplenish All"
        ))
        self.assertTrue(_is_construction_replenish_confirmation(
            "Replenish All\nFollowing resources will be used to replenish missing items.\nConfirm"
        ))

    def test_boomer_auto_join_requires_an_active_timer(self):
        self.assertTrue(_is_boomer_auto_join_enabled("Auto-Join Duration:11:59:59\nQueue No. 4"))
        self.assertFalse(_is_boomer_auto_join_enabled("Auto-Join Duration:Disabled\nQueue No. Disabled"))
