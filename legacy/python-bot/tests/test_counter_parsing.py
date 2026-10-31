import unittest
import logging

import numpy as np

from main_scrcpy import ScrcpyBot
from main_scrcpy import _is_unit_cap_message
from main_scrcpy import _parse_fraction
from main_scrcpy import _parse_power_value


class CounterParsingTests(unittest.TestCase):
    def test_truck_counter(self):
        self.assertEqual(_parse_fraction("Today's Trade Count:4/4"), (4, 4))

    def test_alliance_counter_with_thousands_separator(self):
        self.assertEqual(_parse_fraction("0/1,000"), (0, 1000))

    def test_rejects_impossible_counter(self):
        self.assertIsNone(_parse_fraction("5/4"))

    def test_parses_truck_power_units(self):
        self.assertEqual(_parse_power_value("3.51M"), 3_510_000)
        self.assertEqual(_parse_power_value("428.24M4"), 428_240_000)

    def test_rejects_power_without_unit(self):
        self.assertIsNone(_parse_power_value("unknown"))

    def test_detects_military_center_unit_cap_message(self):
        self.assertTrue(
            _is_unit_cap_message(
                "Unit cap reached. Please upgrade the\n"
                "Military Center to extend the cap."
            )
        )

    def test_rejects_unrelated_upgrade_message(self):
        self.assertFalse(
            _is_unit_cap_message("Please upgrade the Military Center.")
        )


class GatherPanelDetectionTests(unittest.TestCase):
    def setUp(self):
        self.bot = object.__new__(ScrcpyBot)
        self.bot.image_logger = logging.getLogger("test-image")

    def test_detects_light_gather_drawer(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        frame[1340:2120, :] = 220
        self.assertTrue(self.bot._gather_search_panel_visible(frame))

    def test_rejects_world_without_drawer(self):
        frame = np.full((2160, 1080, 3), 80, dtype=np.uint8)
        self.assertFalse(self.bot._gather_search_panel_visible(frame))

    def test_locates_blue_march_button(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        frame[1525:1625, 340:660] = (220, 130, 40)
        self.assertEqual(
            self.bot._locate_gather_march_button(frame),
            (500, 1575),
        )

    def test_rejects_dispatch_screen_without_march_button(self):
        frame = np.full((2160, 1080, 3), 80, dtype=np.uint8)
        self.assertIsNone(self.bot._locate_gather_march_button(frame))


class EndlessNightDetectionTests(unittest.TestCase):
    def setUp(self):
        self.bot = object.__new__(ScrcpyBot)
        self.bot.image_logger = logging.getLogger("test-image")
        template = np.zeros((90, 95, 4), dtype=np.uint8)
        template[:, :, 3] = 0
        template[25:65, 30:65, 3] = 255
        self.bot.templates = {"endless_night_close": template}

    def test_rejects_white_x_match_on_light_mail_panel(self):
        frame = np.full((2160, 1080, 3), 214, dtype=np.uint8)
        self.assertFalse(
            self.bot._endless_night_close_backdrop_visible(frame, (875, 270))
        )

    def test_accepts_white_x_match_on_dark_event_button(self):
        frame = np.full((2160, 1080, 3), 214, dtype=np.uint8)
        frame[270:360, 875:970] = 35
        self.assertTrue(
            self.bot._endless_night_close_backdrop_visible(frame, (875, 270))
        )


if __name__ == "__main__":
    unittest.main()
