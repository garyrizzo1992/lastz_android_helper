"""Keep standalone tools and unrelated legacy state out of the bot repository."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryLayoutTests(unittest.TestCase):
    def test_only_crop_utility_and_required_launcher_remain(self):
        files = {path.name for path in (ROOT / "scripts").iterdir() if path.is_file()}
        self.assertEqual(files, {"scrcpy_crop_screenshot.py", "run_bot.sh"})

    def test_standalone_truck_scanner_is_go_not_python(self):
        self.assertTrue((ROOT/'tools/truck-scanner/go.mod').is_file())
        self.assertTrue((ROOT/'tools/truck-scanner/main.go').is_file())
        self.assertFalse((ROOT/'scripts/scan_trucks.py').exists())

    def test_no_standalone_scrcpy_wrapper_scripts(self):
        wrappers = [path.name for path in (ROOT / "scrcpy").iterdir()
                    if path.suffix in {".py", ".bat", ".vbs"}]
        self.assertEqual(wrappers, [])

    def test_legacy_state_files_are_removed(self):
        for name in ("bot_state.json", "bot_state.json.backup", "bot_state_webstore.json",
                     "ocr_lines.json", "switch_states.json"):
            with self.subTest(name=name):
                self.assertFalse((ROOT / name).exists())

    def test_compatibility_requirements_include_runtime_pins(self):
        content = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("-r requirements-runtime.txt", content)
        self.assertNotIn("playwright", content)
