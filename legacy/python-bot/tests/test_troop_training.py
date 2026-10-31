import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import cv2
import numpy as np

import main_scrcpy
from bot import training


class TroopTierSelectionTests(unittest.TestCase):
    def test_selects_rightmost_colored_card_before_locked_cards(self):
        frame = np.zeros((600, 1000, 3), dtype=np.uint8)
        centers = (100, 300, 500, 700, 900)
        for center in centers[:3]:
            cv2.rectangle(frame, (center - 60, 200), (center + 60, 380), (150, 40, 180), -1)
        for center in centers[3:]:
            cv2.rectangle(frame, (center - 60, 200), (center + 60, 380), (90, 90, 90), -1)
        cv2.rectangle(frame, (410, 170), (590, 410), (0, 210, 255), 8)

        states = main_scrcpy._troop_tier_card_states(
            frame,
            centers,
            card_y=(200, 380),
            half_width=70,
            unlocked_ratio=0.15,
            selected_ratio=0.005,
        )
        highest = main_scrcpy._highest_visible_unlocked_troop_card(states)

        self.assertEqual([state["unlocked"] for state in states], [True, True, True, False, False])
        self.assertEqual(highest["index"], 2)
        self.assertTrue(highest["selected"])

    def test_rightmost_card_wins_when_every_visible_tier_is_unlocked(self):
        states = [
            {"index": 0, "unlocked": True},
            {"index": 1, "unlocked": True},
            {"index": 2, "unlocked": True},
        ]
        self.assertEqual(
            main_scrcpy._highest_visible_unlocked_troop_card(states)["index"],
            2,
        )

    def test_no_colored_tier_fails_closed(self):
        states = [
            {"index": 0, "unlocked": False},
            {"index": 1, "unlocked": False},
        ]
        self.assertIsNone(main_scrcpy._highest_visible_unlocked_troop_card(states))


class TroopTrainingWorkflowTests(unittest.TestCase):
    def test_full_capacity_cooldown_does_not_suppress_collection(self):
        bot=Mock(total_cycles=0,last_2min_action_time=main_scrcpy.time.time(),all_troops_busy=True,
            _perf_metrics={'cycle_times':[]},_cycle_times_by_game={})
        bot._should_check.side_effect=lambda name, interval: name=='train_troops_game1'
        bot.collect_completed_troops.return_value=2
        with patch.object(main_scrcpy.time,'sleep'):
            main_scrcpy.run_one_cycle(bot,'game1')
        bot.collect_completed_troops.assert_called_once_with('game1')
        bot.train_latest_troops.assert_not_called()

    def test_unchanged_marker_is_not_collected_twice_or_reported_successful(self):
        bot=SimpleNamespace(ensure_base_view=Mock(return_value=True),adb_screenshot=Mock(return_value=object()),
            adb_tap=Mock(),game_logger=Mock(),_record_action=Mock())
        with patch.object(training,'_completion_marker',return_value=('raider',700,1200)), patch.object(training.time,'sleep'):
            self.assertEqual(training.collect_completed_troops(bot,'game1'),0)
        bot.adb_tap.assert_called_once()
        self.assertEqual(bot._record_action.call_args.args[2],'failed')

    def test_real_completion_ticks_are_found_without_portrait_match(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        frame=np.zeros((2160,1080,3),dtype=np.uint8)
        frame[1220:1490,590:1000]=cv2.imread(str(root/'tests/fixtures/training_completed_queues.png'))
        bot=SimpleNamespace(find_template=Mock(return_value=None),templates={
            key:cv2.imread(str(root/main_scrcpy.CONFIG['image_paths'][key]),cv2.IMREAD_UNCHANGED)
            for key in ('troop_completion_tick','troop_completion_tick_timer')})
        for center in ((701,1327),(867,1441)):
            match=training._completion_marker(bot,frame,near=center)
            self.assertIsNotNone(match)
            self.assertLess(abs(match[1]-center[0]),10)
        self.assertIsNone(training._completion_marker(bot,np.zeros_like(frame)))
        tick_only=np.zeros_like(frame)
        tick=bot.templates['troop_completion_tick']
        tick_only[1000:1000+tick.shape[0],500:500+tick.shape[1]]=tick[:,:,:3]
        # Only the green shape, without a troop portrait, must be rejected.
        hsv=cv2.cvtColor(tick_only,cv2.COLOR_BGR2HSV)
        tick_only[cv2.inRange(hsv,(35,140,160),(85,255,255))==0]=0
        self.assertIsNone(training._completion_marker(bot,tick_only))

    def test_collects_all_visible_completed_training_buildings(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        bot = SimpleNamespace(
            ensure_base_view=Mock(return_value=True),
            adb_screenshot=Mock(return_value=frame),
            find_template=Mock(
                side_effect=[
                    (700, 1200),  # raider marker
                    None, (850, 1300),  # assulter marker
                    None, None, None,  # no more markers
                ]
            ),
            game_logger=Mock(),
            _record_action=Mock(),
            adb_tap=Mock(),
        )

        with patch.object(main_scrcpy.time, "sleep"), patch.object(training, '_completion_marker',
                side_effect=[('raider',700,1200), None, ('assulter',850,1300), None, None]):
            collected = main_scrcpy.collect_completed_troops(bot, "game4")

        self.assertEqual(collected, 2)
        self.assertEqual(bot._record_action.call_count, 2)
        self.assertEqual(bot.ensure_base_view.call_count, 3)
        bot.adb_tap.assert_has_calls([call(700,1200),call(850,1300)])

    def test_claims_completed_troops_before_selecting_a_new_tier(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        bot = SimpleNamespace(
            ensure_base_view=Mock(return_value=True),
            wait_for_template=Mock(return_value=(700, 1400)),
            adb_screenshot=Mock(return_value=frame),
            adb_tap=Mock(),
            game_logger=Mock(),
            _troop_unit_cap_reached=Mock(return_value=False),
            _record_action=Mock(),
        )

        with (
            patch.object(main_scrcpy, "_find_ocr_word_center", side_effect=[(810, 1710), None, None]),
            patch.object(main_scrcpy.time, "sleep"),
        ):
            result = main_scrcpy.train_latest_troops(bot, "game4")

        self.assertEqual(result, "collected")
        bot.adb_tap.assert_called_once_with(810, 1710)
        bot._record_action.assert_called_once_with(
            "game4", "troop_training_collection", "success",
            "Completed trained troops accepted",
        )
        bot._troop_unit_cap_reached.assert_called_once_with(frame)

    def test_base_return_confirms_training_before_green_base_elements_are_checked(self):
        frame = np.zeros((2160, 1080, 3), dtype=np.uint8)
        states = [
            {"index": 0, "center": (150, 1782), "unlocked": True, "selected": False, "unlocked_score": 0.8},
            {"index": 1, "center": (370, 1782), "unlocked": True, "selected": False, "unlocked_score": 0.7},
            {"index": 2, "center": (585, 1782), "unlocked": True, "selected": True, "unlocked_score": 0.6},
            {"index": 3, "center": (805, 1782), "unlocked": False, "selected": False, "unlocked_score": 0.01},
        ]
        bot = SimpleNamespace(
            ensure_base_view=Mock(return_value=True),
            wait_for_template=Mock(return_value=(700, 1400)),
            adb_screenshot=Mock(return_value=frame),
            adb_tap=Mock(),
            adb_swipe=Mock(),
            game_logger=Mock(),
            _obs_capture=Mock(),
            _troop_unit_cap_reached=Mock(return_value=False),
            _mark_daily_action_complete=Mock(),
            is_screen=Mock(return_value=True),
            confirm_screen=Mock(),
            _record_action=Mock(),
        )

        with (
            patch.object(main_scrcpy, "_troop_tier_card_states", return_value=states),
            patch.object(main_scrcpy, "_find_ocr_word_center", return_value=None),
            patch.object(main_scrcpy, "_ocr_frame_text", return_value=""),
            patch.object(
                main_scrcpy,
                "_locate_green_rect_buttons",
                return_value=[(821, 2065)],
            ) as locate_green,
            patch.object(main_scrcpy.time, "sleep"),
        ):
            result = main_scrcpy.train_latest_troops(bot, "game4")

        self.assertEqual(result, "success")
        bot.confirm_screen.assert_not_called()
        button_geometry = dict(min_width=300, max_width=500, min_height=70, max_height=180)
        self.assertEqual(locate_green.call_args_list, [
            call(frame, (550, 1900, 1080, 2150), **button_geometry),
            call(frame, (550, 1900, 1080, 2150), **button_geometry,
                 hsv_lower=(90, 70, 70), hsv_upper=(130, 255, 255)),
        ])
        bot.adb_tap.assert_has_calls([call(585, 1782), call(821, 2065)])
        bot._record_action.assert_called_once()


if __name__ == "__main__":
    unittest.main()
