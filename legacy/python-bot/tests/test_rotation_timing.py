import unittest

import main_scrcpy


class RotationTimingTests(unittest.TestCase):
    def test_empty_history_has_no_suggestion(self):
        self.assertIsNone(main_scrcpy._rotation_timing_suggestion([]))

    def test_short_cycles_keep_fifteen_minute_floor(self):
        timing = main_scrcpy._rotation_timing_suggestion([180, 210, 240])
        self.assertEqual(timing["p90_seconds"], 240)
        self.assertEqual(timing["recommended_minutes"], 15)

    def test_long_p90_is_buffered_and_rounded(self):
        timing = main_scrcpy._rotation_timing_suggestion([180, 240, 300, 900])
        self.assertEqual(timing["p90_seconds"], 900)
        self.assertEqual(timing["buffered_cycle_seconds"], 1080)
        self.assertEqual(timing["recommended_minutes"], 20)

    def test_recommendation_obeys_configured_ceiling(self):
        timing = main_scrcpy._rotation_timing_suggestion(
            [3600],
            {
                "rotation_suggestion_min_minutes": 15,
                "rotation_suggestion_max_minutes": 30,
                "rotation_suggestion_round_minutes": 5,
                "rotation_cycle_buffer_ratio": 1.2,
            },
        )
        self.assertEqual(timing["recommended_minutes"], 30)


if __name__ == "__main__":
    unittest.main()
