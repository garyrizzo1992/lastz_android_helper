import unittest
from unittest.mock import patch

import cv2
import numpy as np

from main_scrcpy import (
    _find_ocr_word_center,
    _find_world_bounty_markers,
    _world_coordinate_form_visible,
    _world_info_card_visible,
)


class WorldBountyMarkerTests(unittest.TestCase):
    def make_frame(self):
        frame = np.full((2160, 1080, 3), (85, 105, 85), dtype=np.uint8)
        return frame

    @staticmethod
    def draw_marker(frame, center, color):
        x, y = center
        cv2.ellipse(frame, (x, y), (30, 22), 0, 0, 360, color, -1)
        cv2.ellipse(frame, (x, y + 42), (34, 15), 0, 0, 360, (35, 35, 35), -1)
        cv2.putText(
            frame,
            "6",
            (x - 8, y + 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (245, 245, 245),
            2,
            cv2.LINE_AA,
        )

    def test_detects_purple_blue_and_orange_markers_with_level_badges(self):
        frame = self.make_frame()
        self.draw_marker(frame, (260, 650), (190, 45, 185))   # purple
        self.draw_marker(frame, (500, 900), (225, 105, 25))   # blue
        self.draw_marker(frame, (650, 1250), (0, 145, 255))   # orange

        markers = _find_world_bounty_markers(frame)

        self.assertEqual({item["color"] for item in markers}, {"purple", "blue", "orange"})
        self.assertEqual([item["color"] for item in markers], ["purple", "blue", "orange"])
        centers = [item["center"] for item in markers]
        for expected_x, expected_y in ((260, 650), (500, 900), (650, 1250)):
            self.assertTrue(
                any(abs(x - expected_x) <= 5 and abs(y - expected_y) <= 5 for x, y in centers)
            )

    def test_rejects_coloured_blob_without_dark_level_badge(self):
        frame = self.make_frame()
        cv2.ellipse(frame, (450, 800), (35, 25), 0, 0, 360, (190, 45, 185), -1)

        self.assertEqual(_find_world_bounty_markers(frame), [])

    def test_ignores_matching_hud_colour_outside_safe_scan_roi(self):
        frame = self.make_frame()
        self.draw_marker(frame, (980, 500), (0, 145, 255))

        self.assertEqual(_find_world_bounty_markers(frame), [])

    def test_overlapping_colour_components_are_deduplicated(self):
        frame = self.make_frame()
        self.draw_marker(frame, (500, 800), (190, 45, 185))
        cv2.circle(frame, (515, 800), 14, (225, 105, 25), -1)

        markers = _find_world_bounty_markers(frame)

        self.assertEqual(len(markers), 1)

    def test_detects_light_map_info_card(self):
        frame = self.make_frame()
        frame[520:980, 0:650] = (210, 220, 225)

        self.assertTrue(_world_info_card_visible(frame))

    def test_does_not_treat_plain_terrain_as_info_card(self):
        self.assertFalse(_world_info_card_visible(self.make_frame()))

    def test_detects_blue_coordinate_submit_button(self):
        frame = self.make_frame()
        frame[240:325, 805:885] = (230, 135, 35)

        self.assertTrue(_world_coordinate_form_visible(frame))

    def test_plain_map_has_no_coordinate_submit_button(self):
        self.assertFalse(_world_coordinate_form_visible(self.make_frame()))


class WorldBountyOcrTests(unittest.TestCase):
    def test_returns_screen_coordinates_for_plunder_word(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        fake_data = {
            "text": ["", "Plunder"],
            "left": [0, 100],
            "top": [0, 80],
            "width": [0, 120],
            "height": [0, 40],
        }
        with patch("main_scrcpy.pytesseract.image_to_data", return_value=fake_data):
            center = _find_ocr_word_center(frame, "plunder", (80, 700, 1000, 1900))

        # OCR coordinates are on the 2x enlarged ROI.
        self.assertEqual(center, (160, 750))


if __name__ == "__main__":
    unittest.main()
