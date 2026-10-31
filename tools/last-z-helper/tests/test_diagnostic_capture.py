"""Metadata diagnostics must not retain unrelated screen contents implicitly."""
import contextlib
import io
from pathlib import Path
import runpy
import shlex
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class DiagnosticCaptureTests(unittest.TestCase):
    def invoke(self, *args):
        with patch.object(sys, "argv", ["phone_check.py", *args]), patch("subprocess.run") as command:
            runpy.run_path(str(ROOT / "phone_check.py"), run_name="__main__")
        # Parse the two actual shell quoting layers, rather than substring matching.
        inner = shlex.split(command.call_args.args[0][-1])[2]
        words = shlex.split(inner)
        return words[words.index("dev.codex.lastzhelper.PhoneCheck") + 1:]

    def test_default_metadata_check_does_not_capture(self):
        args = self.invoke("ui-bounds", "--path", "UIManagerInstance/windows/Example/View/button")
        self.assertEqual(args, ["/data/local/tmp/lastz-phone-check", "ui-bounds", "UIManagerInstance/windows/Example/View/button", "", "0"])

    def test_explicit_capture_preserves_existing_argument_positions(self):
        args = self.invoke("ui-bounds", "--path", "UIManagerInstance/windows/Example/View/button", "--child", "Child With Spaces", "--parent", "2", "--screenshot")
        self.assertEqual(args[-4:], ["UIManagerInstance/windows/Example/View/button", "Child With Spaces", "2", "--screenshot"])

    def test_capture_is_rejected_for_memory_query_before_any_device_command(self):
        with patch.object(sys, "argv", ["phone_check.py", "query", "--screenshot"]), patch("subprocess.run") as command, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                runpy.run_path(str(ROOT / "phone_check.py"), run_name="__main__")
            self.assertEqual(raised.exception.code, 2)
            command.assert_not_called()

    def test_native_diagnostic_capture_has_explicit_opt_in_gate(self):
        source = (ROOT / "src/dev/codex/lastzhelper/PhoneCheck.java").read_text(encoding="utf-8")
        self.assertEqual(source.count('screenshot("before.png")'), 1)
        self.assertIn('if(args.length>2&&"--screenshot".equals(args[args.length-1]))c.input.screenshot("before.png")', source)


if __name__ == "__main__":
    unittest.main()
