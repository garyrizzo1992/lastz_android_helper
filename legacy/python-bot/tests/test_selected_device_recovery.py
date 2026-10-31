import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from bot.android import AndroidMixin, get_device_id


class SelectedDeviceRecoveryTests(unittest.TestCase):
    def bot(self):
        return SimpleNamespace(
            device_id="selected-phone", _adb_recovering=False,
            _last_adb_recovery_ts=0, _consecutive_screenshot_failures=3,
            adb_logger=Mock(), _invalidate_screenshot=Mock(), _obs_event=Mock(),
        )

    def recover(self, bot, **kwargs):
        context = SimpleNamespace(CONFIG={}, _resolve_adb=Mock(return_value="adb-test"), get_device_id=Mock())
        with patch("bot.android.context", new=context), patch("bot.android.subprocess.run", **kwargs) as command:
            result = AndroidMixin._recover_adb_device(bot, "test")
            context.get_device_id.assert_not_called()
        return result, command

    def test_reconnected_selected_serial_is_reused_without_discovery(self):
        bot = self.bot()
        result, command = self.recover(bot, return_value=SimpleNamespace(returncode=0, stdout="device\n"))
        self.assertTrue(result)
        self.assertEqual(command.call_args.args[0], ["adb-test", "-s", "selected-phone", "get-state"])
        self.assertEqual(bot.device_id, "selected-phone")
        self.assertEqual(bot._consecutive_screenshot_failures, 0)
        bot._invalidate_screenshot.assert_called_once()
        self.assertFalse(bot._adb_recovering)

    def test_missing_offline_or_unauthorized_device_never_rebinds(self):
        for code, state in [(1, ""), (0, "offline"), (0, "unauthorized")]:
            with self.subTest(state=state):
                bot = self.bot()
                result, _ = self.recover(bot, return_value=SimpleNamespace(returncode=code, stdout=state))
                self.assertFalse(result)
                self.assertEqual(bot.device_id, "selected-phone")
                bot._obs_event.assert_not_called()
                self.assertEqual(bot._consecutive_screenshot_failures, 3)
                self.assertFalse(bot._adb_recovering)

    def test_timeout_does_not_switch_or_report_recovery(self):
        bot = self.bot()
        result, _ = self.recover(bot, side_effect=subprocess.TimeoutExpired("adb-test", 5))
        self.assertFalse(result)
        self.assertEqual(bot.device_id, "selected-phone")
        bot._obs_event.assert_not_called()
        self.assertFalse(bot._adb_recovering)

    def test_changed_session_during_probe_is_rejected(self):
        bot = self.bot()
        def probe(*args, **kwargs):
            bot.device_id = "externally-changed"
            return SimpleNamespace(returncode=0, stdout="device")
        result, _ = self.recover(bot, side_effect=probe)
        self.assertFalse(result)
        bot._obs_event.assert_not_called()
        self.assertFalse(bot._adb_recovering)


class DeviceStartupSelectionTests(unittest.TestCase):
    def discover(self, devices, models, serial="", model="Expected", config_serial=""):
        calls = []
        def run(args, **kwargs):
            calls.append(args)
            if args[-1] == "devices":
                return SimpleNamespace(stdout="List of devices attached\n" + devices)
            return SimpleNamespace(stdout=models[args[2]])
        context = SimpleNamespace(CONFIG={"device_model": model, "device_serial": config_serial}, _resolve_adb=Mock(return_value="adb-test"))
        with patch("bot.android.context", new=context), patch.dict("os.environ", {"LASTZ_DEVICE_SERIAL": serial}), patch("bot.android.subprocess.run", side_effect=run), patch("bot.android.logging.getLogger", return_value=Mock()):
            result = get_device_id(retries=1, delay=0)
        return result, calls

    def test_explicit_device_does_not_query_other_models(self):
        result, calls = self.discover("chosen device\nother device\n", {}, serial="chosen")
        self.assertEqual(result, "chosen")
        self.assertEqual(len(calls), 1)

    def test_missing_explicit_device_never_falls_back(self):
        result, calls = self.discover("other device\n", {}, serial="missing")
        self.assertIsNone(result)
        self.assertEqual(len(calls), 1)

    def test_multiple_model_matches_are_rejected(self):
        result, _ = self.discover("one device\ntwo device\n", {"one": "Expected", "two": "Expected"})
        self.assertIsNone(result)

    def test_unique_model_match_is_selected(self):
        result, _ = self.discover("one device\ntwo device\n", {"one": "Different", "two": "Expected"})
        self.assertEqual(result, "two")

    def test_model_mismatch_or_unauthorized_device_is_not_selected(self):
        result, _ = self.discover("one device\ntwo unauthorized\n", {"one": "Different"})
        self.assertIsNone(result)

    def test_environment_serial_overrides_configured_serial(self):
        result, calls = self.discover("environment device\nconfigured device\n", {}, serial="environment", config_serial="configured")
        self.assertEqual(result, "environment")
        self.assertEqual(len(calls), 1)

    def test_config_serial_used_when_environment_has_no_selection(self):
        result, calls = self.discover("configured device\nother device\n", {}, config_serial="configured")
        self.assertEqual(result, "configured")
        self.assertEqual(len(calls), 1)

    def test_unavailable_environment_serial_does_not_fall_back_to_config(self):
        result, calls = self.discover("configured device\n", {}, serial="missing", config_serial="configured")
        self.assertIsNone(result)
        self.assertEqual(len(calls), 1)

    def test_discovery_timeout_retries_with_bounded_timeout_and_no_model_probe(self):
        context = SimpleNamespace(CONFIG={"device_serial": "chosen"}, _resolve_adb=Mock(return_value="adb-test"))
        with patch("bot.android.context", new=context), patch.dict("os.environ", {"LASTZ_DEVICE_SERIAL": ""}), patch(
            "bot.android.subprocess.run", side_effect=subprocess.TimeoutExpired("adb-test", 10)
        ) as command, patch("bot.android.time.sleep") as sleep, patch("bot.android.logging.getLogger", return_value=Mock()):
            self.assertIsNone(get_device_id(retries=2, delay=0.1))
        self.assertEqual(command.call_count, 2)
        for call in command.call_args_list:
            self.assertEqual(call.args[0], ["adb-test", "devices"])
            self.assertEqual(call.kwargs["timeout"], 10)
        sleep.assert_called_once_with(0.1)

    def test_model_probe_timeout_does_not_fallback_to_unknown_model(self):
        def probe(args, **kwargs):
            if args[-1] == "devices":
                return SimpleNamespace(stdout="List of devices attached\none device\n")
            self.assertEqual(kwargs["timeout"], 5)
            raise subprocess.TimeoutExpired("adb-test", 5)
        context = SimpleNamespace(CONFIG={"device_model": "Expected"}, _resolve_adb=Mock(return_value="adb-test"))
        with patch("bot.android.context", new=context), patch.dict("os.environ", {"LASTZ_DEVICE_SERIAL": ""}), patch("bot.android.subprocess.run", side_effect=probe), patch("bot.android.logging.getLogger", return_value=Mock()):
            self.assertIsNone(get_device_id(retries=1, delay=0))


if __name__ == "__main__":
    unittest.main()
