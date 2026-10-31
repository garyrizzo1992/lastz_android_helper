import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import main_scrcpy


ROOT = Path(__file__).resolve().parents[1]


def detected_home(*, ok=True, matches=2, score=0.82):
    return {
        "screen": "home" if ok else None,
        "checks": [
            {
                "screen": "home",
                "ok": ok,
                "matches": matches,
                "score": score,
            }
        ],
    }


class BaseRecoveryEvidenceTests(unittest.TestCase):
    def test_current_marker_and_home_hud_are_a_candidate(self):
        evidence = main_scrcpy._base_recovery_evidence(
            detected_home(matches=1),
            home_marker_visible=True,
            home_marker_seen_at=None,
            now=100.0,
        )
        self.assertTrue(evidence["candidate"])

    def test_recent_animated_marker_remains_valid_with_strong_hud(self):
        evidence = main_scrcpy._base_recovery_evidence(
            detected_home(matches=2),
            home_marker_visible=False,
            home_marker_seen_at=95.0,
            now=100.0,
            marker_grace_seconds=8.0,
        )
        self.assertTrue(evidence["candidate"])
        self.assertTrue(evidence["marker_recent"])

    def test_strong_home_hud_confirms_without_an_animated_marker(self):
        evidence = main_scrcpy._base_recovery_evidence(
            detected_home(matches=2),
            home_marker_visible=False,
            home_marker_seen_at=90.0,
            now=100.0,
            marker_grace_seconds=8.0,
        )
        self.assertTrue(evidence["candidate"])
        self.assertFalse(evidence["marker_recent"])

    def test_marker_alone_cannot_confirm_wrong_hud(self):
        evidence = main_scrcpy._base_recovery_evidence(
            detected_home(ok=False, matches=0),
            home_marker_visible=True,
            home_marker_seen_at=100.0,
            now=100.0,
        )
        self.assertFalse(evidence["candidate"])


class RuntimeAssetTests(unittest.TestCase):
    def test_all_configured_runtime_images_exist(self):
        configured_paths = {
            **main_scrcpy.CONFIG["image_paths"],
            **{
                f"screen_sanity:{name}": config["path"]
                for name, config in main_scrcpy.CONFIG["screen_sanity"].items()
            },
        }
        missing = {
            name: path
            for name, path in configured_paths.items()
            if not (ROOT / path).is_file()
        }

        self.assertEqual({}, missing)

class FeatureGateTests(unittest.TestCase):
    def test_removed_bounty_counter_helpers_are_not_registered(self):
        for name in ("parse_bounty_counters", "_ocr_bounty_counter", "_visual_bounty_counter", "_obs_step"):
            with self.subTest(name=name):
                self.assertFalse(hasattr(main_scrcpy.ScrcpyBot, name))
                self.assertNotIn(name, main_scrcpy.HELPER_METHOD_NAMES)

    def test_obsolete_settings_are_removed(self):
        for name in (
            "bounty_counter_rois", "scrcpy_path", "scrcpy_linux_path",
            "alliance_help_counter_roi", "trucks_wait_until_reset",
        ):
            with self.subTest(name=name):
                self.assertNotIn(name, main_scrcpy.CONFIG)

    def test_personal_bounties_use_shortcut_and_world_stays_off(self):
        self.assertFalse(hasattr(main_scrcpy, "do_bounty"))
        self.assertNotIn("do_bounty", main_scrcpy.HELPER_METHOD_NAMES)
        self.assertNotIn("do_bounty", main_scrcpy.run_one_cycle.__code__.co_names)
        self.assertNotIn("bounty_enabled", main_scrcpy.CONFIG)
        self.assertIn('do_personal_bounties', main_scrcpy.HELPER_METHOD_NAMES)
        self.assertIn('do_personal_bounties', main_scrcpy.run_one_cycle.__code__.co_names)
        self.assertTrue(main_scrcpy.CONFIG['personal_bounties']['enabled'])
        self.assertFalse(main_scrcpy.CONFIG["world_bounty"]["enabled"])


class WorldScreenFallbackTests(unittest.TestCase):
    def test_static_hq_control_short_circuits_slow_sidebar_ocr(self):
        read_march_status = Mock(
            side_effect=AssertionError("OCR must not run after a definitive template")
        )
        fake_bot = SimpleNamespace(
            screen_sanity=Mock(return_value={"ok": False}),
            find_template=Mock(
                side_effect=lambda name, _frame, click=False: (900, 2000)
                if name == "hq"
                else None
            ),
            read_march_status=read_march_status,
        )

        self.assertTrue(
            main_scrcpy.ScrcpyBot.is_screen(fake_bot, "world", object())
        )
        read_march_status.assert_not_called()


class AdbScreenshotTimeoutTests(unittest.TestCase):
    def test_screencap_timeout_is_bounded_and_reported(self):
        with patch.object(main_scrcpy, "_resolve_adb", return_value="adb"), patch.object(
            main_scrcpy.subprocess,
            "run",
            side_effect=main_scrcpy.subprocess.TimeoutExpired(["adb"], 12.0),
        ) as run:
            with self.assertRaisesRegex(RuntimeError, "timed out after 12.0s"):
                main_scrcpy.capture_device_screen("device-1")

        self.assertEqual(run.call_args.kwargs["timeout"], 12.0)


if __name__ == "__main__":
    unittest.main()
