import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from bot.android import adb_command, _adb_log_category


class AdbLogMinimizationTests(unittest.TestCase):
    def test_categories_never_retain_payload_paths_or_unknown_verbs(self):
        for args in [("shell", "input", "text", "private-message"),
                     ("shell", "input text private-message"),
                     ("push", "private-message", "/sdcard/private-message"),
                     ("private-message",)]:
            self.assertNotIn("private-message", _adb_log_category(args))
        self.assertIn("shell input", _adb_log_category(("shell", "input", "text", "x")))

    def invoke(self, **kwargs):
        bot = SimpleNamespace(_perf_metrics={"adb_commands": 0}, device_id="private-serial",
                              adb_logger=Mock(), _recover_adb_device=Mock())
        context = SimpleNamespace(_resolve_adb=Mock(return_value="private-adb-path"))
        with patch("bot.android.context", new=context), patch("bot.android.subprocess.run", **kwargs) as run:
            result = adb_command(bot, "shell", "input", "text", "private-message")
        logs = repr(bot.adb_logger.mock_calls)
        for secret in ["private-message", "private-serial", "private-adb-path", "private-stderr"]:
            self.assertNotIn(secret, logs)
        self.assertEqual(run.call_args.args[0][-1], "private-message")
        return bot, result

    def test_execution_receives_payload_but_logs_do_not(self):
        response = SimpleNamespace(returncode=0, stdout="", stderr="")
        _, result = self.invoke(return_value=response)
        self.assertIs(result, response)

    def test_transport_failure_logs_no_raw_stderr_and_keeps_recovery_signal(self):
        response = SimpleNamespace(returncode=1, stdout="", stderr="device offline private-stderr")
        bot, _ = self.invoke(return_value=response)
        bot._recover_adb_device.assert_called_once_with(reason="adb_transport_unavailable")

    def test_exception_details_cannot_echo_command_payload(self):
        _, result = self.invoke(side_effect=RuntimeError("private-message private-stderr"))
        self.assertIsNone(result)

    def test_timeout_keeps_payload_out_of_logs(self):
        _, result = self.invoke(side_effect=subprocess.TimeoutExpired("private-message", 10))
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
