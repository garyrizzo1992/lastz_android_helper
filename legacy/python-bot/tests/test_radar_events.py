import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import cv2
import numpy as np

import main_scrcpy


class RadarEventDetectionTests(unittest.TestCase):
    def test_pickaxe_matching_is_color_independent_and_finds_multiple_markers(self):
        template_path = (
            Path(main_scrcpy.__file__).parent
            / "images"
            / "radar_events"
            / "radar_event_pickaxe.png"
        )
        template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
        self.assertIsNotNone(template)

        frame = np.zeros((500, 600, 3), dtype=np.uint8)
        frame[100:200, 100:200] = template
        gray_variant = cv2.cvtColor(
            cv2.cvtColor(template, cv2.COLOR_BGR2GRAY),
            cv2.COLOR_GRAY2BGR,
        )
        frame[260:360, 350:450] = gray_variant

        matches = main_scrcpy._template_match_centers(
            frame,
            template,
            (0, 0, 600, 500),
            threshold=0.85,
            max_matches=4,
        )

        centers = {(x, y) for x, y, _score in matches}
        self.assertIn((150, 150), centers)
        self.assertIn((400, 310), centers)


class TroopCapacityTests(unittest.TestCase):
    def test_reads_zero_selected_capacity(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        with patch.object(
            main_scrcpy.pytesseract,
            "image_to_string",
            return_value="0/1,181",
        ):
            self.assertEqual(
                main_scrcpy._ocr_troop_capacity(
                    frame,
                    ((420, 1215, 600, 1280),),
                ),
                (0, 1181),
            )

    def test_radar_event_never_taps_march_with_zero_capacity(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        bot = SimpleNamespace(
            templates={"radar_event_pickaxe": np.zeros((100, 100, 3), dtype=np.uint8)},
            ensure_base_view=Mock(return_value=True),
            adb_screenshot=Mock(return_value=frame),
            find_template=Mock(return_value=(10, 10)),
            is_screen=Mock(return_value=True),
            adb_tap=Mock(),
            read_march_status=Mock(return_value={"count": {"used": 2, "total": 3}}),
            march_slots_full=Mock(return_value=False),
            march_dispatch_confirmed=Mock(),
            game_logger=Mock(),
            _record_action=Mock(),
            _obs_capture=Mock(),
        )
        test_cfg = {
            "enabled": True,
            "max_events_per_check": 1,
            "marker_roi": (0, 0, 1080, 1800),
            "detail_text_roi": (0, 0, 1080, 1800),
            "go_button": (540, 2045),
            "attack_word_roi": (0, 0, 1080, 1800),
            "march_word_roi": (0, 0, 1080, 1800),
            "troop_capacity_value_rois": ((420, 1215, 600, 1280),),
            "post_go_delay": 0,
            "post_attack_delay": 0,
            "events": (
                {
                    "kind": "pickaxe",
                    "template": "radar_event_pickaxe",
                    "threshold": 0.85,
                    "detail_keywords": ("battle the bloods",),
                },
            ),
        }

        with (
            patch.dict(main_scrcpy.CONFIG, {"radar_events": test_cfg}),
            patch.object(
                main_scrcpy,
                "_template_match_centers",
                return_value=[(500, 800, 0.99)],
            ),
            patch.object(
                main_scrcpy,
                "_ocr_frame_text",
                return_value="Battle the Bloods for resources",
            ),
            patch.object(
                main_scrcpy,
                "_find_ocr_word_center",
                return_value=(540, 1450),
            ) as find_word,
            patch.object(
                main_scrcpy,
                "_ocr_troop_capacity",
                return_value=(0, 1181),
            ),
        ):
            dispatched = main_scrcpy.process_radar_events(bot, "game4")

        self.assertEqual(dispatched, 0)
        self.assertEqual(find_word.call_count, 1)
        bot.march_dispatch_confirmed.assert_not_called()

    def test_radar_uses_visual_march_button_when_ocr_misses_the_label(self):
        self._assert_visual_march_fallback(blue=False)

    def test_radar_uses_blue_button_after_green_detection_misses(self):
        self._assert_visual_march_fallback(blue=True)

    def _assert_visual_march_fallback(self, blue):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        before = {"count": {"used": 1, "total": 3}}
        after = {"count": {"used": 2, "total": 3}}
        bot = SimpleNamespace(
            templates={"radar_event_pickaxe": np.zeros((100, 100, 3), dtype=np.uint8)},
            ensure_base_view=Mock(return_value=True),
            adb_screenshot=Mock(return_value=frame),
            find_template=Mock(return_value=(10, 10)),
            is_screen=Mock(return_value=True),
            adb_tap=Mock(),
            read_march_status=Mock(side_effect=[before, after]),
            march_slots_full=Mock(return_value=False),
            march_dispatch_confirmed=Mock(return_value=(True, "used_increased")),
            game_logger=Mock(),
            _record_action=Mock(),
            _obs_capture=Mock(),
        )
        test_cfg = {
            "enabled": True,
            "max_events_per_check": 1,
            "marker_roi": (0, 0, 1080, 1800),
            "detail_text_roi": (0, 0, 1080, 1800),
            "go_button": (540, 2045),
            "attack_word_roi": (0, 0, 1080, 1800),
            "march_word_roi": (0, 0, 1080, 1800),
            "march_button_roi": (250, 1350, 750, 1750),
            "post_go_delay": 0,
            "post_attack_delay": 0,
            "post_march_delay": 0,
            "events": (
                {
                    "kind": "pickaxe",
                    "template": "radar_event_pickaxe",
                    "threshold": 0.85,
                    "detail_keywords": ("battle the bloods",),
                },
            ),
        }

        with (
            patch.dict(main_scrcpy.CONFIG, {"radar_events": test_cfg}),
            patch.object(main_scrcpy, "_template_match_centers", return_value=[(500, 800, 0.99)]),
            patch.object(main_scrcpy, "_ocr_frame_text", return_value="unreadable event text"),
            patch.object(main_scrcpy, "_find_ocr_word_center", side_effect=[(540, 1450), None]),
            patch.object(main_scrcpy, "_ocr_troop_capacity", return_value=(100, 1181)),
            patch.object(main_scrcpy, "_locate_green_rect_buttons", return_value=[(510, 1570)],
                         side_effect=[[], [(510,1570)]] if blue else None),
            patch.object(main_scrcpy.time, "sleep"),
        ):
            dispatched = main_scrcpy.process_radar_events(bot, "game4")

        self.assertEqual(dispatched, 1)
        bot.adb_tap.assert_any_call(510, 1570)


if __name__ == "__main__":
    unittest.main()
