import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main_scrcpy


class HostPathTests(unittest.TestCase):
    def test_relative_runtime_override_is_rooted_at_repository(self):
        with patch.dict(os.environ, {"LASTZ_TEST_PATH": "host-data/logs"}):
            result = main_scrcpy._host_path("LASTZ_TEST_PATH", "unused")
        self.assertEqual(result, (main_scrcpy.PROJECT_ROOT / "host-data" / "logs").resolve())

    def test_default_runtime_paths_are_absolute(self):
        self.assertTrue(Path(main_scrcpy.CONFIG["logs_dir"]).is_absolute())
        self.assertTrue(Path(main_scrcpy.CONFIG["debug_dir"]).is_absolute())
        self.assertTrue(Path(main_scrcpy.CONFIG["status_file"]).is_absolute())


class ExecutableResolutionTests(unittest.TestCase):
    def test_adb_environment_override_takes_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "adb-test"
            executable.touch()
            with (
                patch.dict(os.environ, {"LASTZ_ADB_PATH": str(executable)}, clear=False),
                patch("main_scrcpy._is_usable_adb_candidate", return_value=True),
            ):
                self.assertEqual(main_scrcpy._resolve_adb(), str(executable.resolve()))

    def test_tesseract_environment_override_takes_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "tesseract-test"
            executable.touch()
            with patch.dict(
                os.environ,
                {"LASTZ_TESSERACT_PATH": str(executable)},
                clear=False,
            ):
                self.assertEqual(
                    main_scrcpy._resolve_tesseract(),
                    str(executable.resolve()),
                )


if __name__ == "__main__":
    unittest.main()
