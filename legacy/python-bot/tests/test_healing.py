import unittest
from unittest.mock import patch

import cv2
import numpy as np

import main_scrcpy
from bot import healing
from types import SimpleNamespace
from unittest.mock import Mock


class HealingDurationTests(unittest.TestCase):
    def test_slider_interpolates_after_bracketing_target(self):
        next_x, lower, upper = main_scrcpy._next_healing_slider_position(
            404, 6634, 7200, 358, 642
        )
        self.assertEqual(next_x, 423)
        self.assertEqual(lower, (404, 6634))
        self.assertIsNone(upper)

        next_x, lower, upper = main_scrcpy._next_healing_slider_position(
            423, 9270, 7200, 358, 642, lower, upper
        )
        self.assertEqual(next_x, 408)
        self.assertEqual(upper, (423, 9270))

    def test_parses_hour_timer(self):
        self.assertEqual(main_scrcpy._parse_healing_duration_seconds("01:01:48"), 3708)

    def test_repairs_ocr_letter_o(self):
        self.assertEqual(main_scrcpy._parse_healing_duration_seconds("O0:26:43"), 1603)

    def test_parses_minute_timer(self):
        self.assertEqual(main_scrcpy._parse_healing_duration_seconds("26:43"), 1603)

    def test_rejects_invalid_timer(self):
        self.assertIsNone(main_scrcpy._parse_healing_duration_seconds("No unit selected"))

    @patch("main_scrcpy.pytesseract.image_to_string", return_value="Heal\n00:29:41")
    def test_reads_duration_from_heal_button_roi(self, _ocr):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        self.assertEqual(
            main_scrcpy._ocr_healing_duration_seconds(frame, (730, 1850, 960, 1940)),
            1781,
        )

    def test_slider_coordinates_target_native_handle_centres(self):
        healing = main_scrcpy.CONFIG["healing"]
        self.assertEqual(healing["hospital_slider_y"], (755, 973, 1191, 1409))
        self.assertEqual(healing["hospital_slider_min_x"], 358)
        self.assertEqual(healing["hospital_slider_max_x"], 642)
        actions = main_scrcpy.CONFIG["action_coords"]
        self.assertEqual(actions["hospital_select_all"], (220, 1875))
        self.assertEqual(actions["hospital_heal_confirm"], (860, 1875))


class HealingVisionTests(unittest.TestCase):
    def test_heal_tap_without_active_state_is_not_success(self):
        bot=SimpleNamespace(templates={},adb_screenshot=Mock(return_value=None))
        with patch.object(main_scrcpy,'_find_masked_template_in_roi',return_value=None), patch.object(healing.time,'sleep'):
            state,_,_=healing._verify_healing_start(bot,None,main_scrcpy.CONFIG['healing'])
        self.assertIsNone(state)
        self.assertEqual(bot.adb_screenshot.call_count,3)

    def test_healing_confirmation_waits_for_toolbar_transition(self):
        bot=SimpleNamespace(templates={},adb_screenshot=Mock(return_value='new frame'))
        with patch.object(main_scrcpy,'_find_masked_template_in_roi',side_effect=[None,None,(50,1600)]), patch.object(healing.time,'sleep'):
            state,frame,_=healing._verify_healing_start(bot,'old frame',main_scrcpy.CONFIG['healing'])
        self.assertEqual((state,frame),('heal_help_state','new frame'))

    def test_all_three_healing_completion_portraits_are_matchable(self):
        names = main_scrcpy.CONFIG["healing"]["completion_templates"]
        self.assertEqual(len(names), 3)
        self.assertEqual(
            main_scrcpy.CONFIG["image_paths"]["heal_complete_brutal"],
            "images/archive/heal/accept1.png",
        )

        for name in names:
            template = cv2.imread(
                main_scrcpy.CONFIG["image_paths"][name], cv2.IMREAD_UNCHANGED
            )
            self.assertIsNotNone(template, name)
            frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
            # The live toolbar can place its completion portrait as far right
            # as x=322; the ROI must include the whole icon at that position.
            top, left = 1600, 322
            height, width = template.shape[:2]
            frame[top:top + height, left:left + width] = template[:, :, :3]

            match = main_scrcpy._find_masked_template_in_roi(
                frame,
                template,
                main_scrcpy.CONFIG["healing"]["world_icon_roi"],
                main_scrcpy.CONFIG["healing"]["completion_match_score"],
            )
            self.assertIsNotNone(match, name)

    @patch(
        "main_scrcpy._ocr_frame_text",
        return_value='Gomz\nSpeedup Duration\n44m\nInspired by "Ode to Revival"\nConfirm',
    )
    def test_detects_variable_alliance_speedup_reward(self, _ocr):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        frame[400:1500, 120:960] = (0, 128, 255)
        self.assertTrue(main_scrcpy._is_alliance_speedup_reward_dialog(frame))

    @patch("main_scrcpy._ocr_frame_text", return_value="Confirm healing 02:00:00")
    def test_rejects_unrelated_confirmation(self, _ocr):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        frame[400:1500, 120:960] = (0, 128, 255)
        self.assertFalse(main_scrcpy._is_alliance_speedup_reward_dialog(frame))

    @patch("main_scrcpy._ocr_frame_text")
    def test_reward_dialog_skips_ocr_without_orange_panel(self, ocr):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        self.assertFalse(main_scrcpy._is_alliance_speedup_reward_dialog(frame))
        ocr.assert_not_called()

    def test_world_healing_state_templates_are_distinct(self):
        names = ("heal_idle", "heal_active", "heal_help_state")
        templates = {
            name: cv2.imread(
                main_scrcpy.CONFIG["image_paths"][name], cv2.IMREAD_UNCHANGED
            )
            for name in names
        }
        self.assertTrue(all(template is not None for template in templates.values()))

        for state_name, state in templates.items():
            frame = state[:, :, :3]
            roi = (0, 0, frame.shape[1], frame.shape[0])
            for template_name, template in templates.items():
                match = main_scrcpy._find_masked_template_in_roi(
                    frame, template, roi, 0.03
                )
                if template_name == state_name:
                    self.assertIsNotNone(match)
                else:
                    self.assertIsNone(match)

    def test_masked_match_is_scoped_to_roi(self):
        frame = np.zeros((120, 120, 3), dtype=np.uint8)
        template = np.zeros((12, 10, 4), dtype=np.uint8)
        template[:, :, :3] = (20, 100, 230)
        template[:, :, 3] = 255
        frame[70:82, 60:70] = template[:, :, :3]

        match = main_scrcpy._find_masked_template_in_roi(
            frame, template, (40, 50, 90, 100), 0.01
        )
        self.assertIsNotNone(match)
        self.assertEqual(match[:2], (60, 70))
        self.assertIsNone(
            main_scrcpy._find_masked_template_in_roi(
                frame, template, (0, 0, 40, 40), 0.01
            )
        )

    @patch("main_scrcpy.pytesseract.image_to_data")
    def test_hospital_rows_choose_visible_available_counts(self, image_to_data):
        image_to_data.return_value = {
            "text": ["3", "19", "396", "120", "0"],
            "left": [172, 317, 311, 186, 600],
            "top": [69, 287, 505, 723, 790],
        }
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        counts = main_scrcpy._hospital_row_availability(
            frame, (669, 887, 1105, 1323)
        )
        self.assertEqual(counts, [3, 19, 396, 120])
        self.assertEqual(max(range(len(counts)), key=counts.__getitem__), 2)


if __name__ == "__main__":
    unittest.main()
