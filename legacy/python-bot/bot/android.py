"""Android services extracted from the application facade."""
import cv2
import numpy as np
import time
import subprocess
import random
import os
import sys
import platform
import logging
import pytesseract
import re
from pathlib import Path
import shutil
import tempfile
from bot.context import context


def get_device_id(retries: int = 5, delay: float = 2.0):
    """Select an explicit authorized serial or one unambiguous model match.

    LASTZ_DEVICE_SERIAL takes precedence over CONFIG["device_serial"]. A missing
    explicit device, model mismatch or multiple matching devices fails closed;
    no available-device fallback is permitted. This selects a transport, not a
    game account or shared-controller lease.
    """
    logger = logging.getLogger('adb')
    adb = context._resolve_adb()
    if not adb:
        logger.critical("adb not found. Install platform-tools or set LASTZ_ADB_PATH.")
        return None
    expected_serial = str(os.environ.get("LASTZ_DEVICE_SERIAL") or context.CONFIG.get("device_serial", "") or "").strip()
    expected_model = str(context.CONFIG.get("device_model", "") or "").strip()
    if not expected_serial and not expected_model:
        logger.error("Select LASTZ_DEVICE_SERIAL or configure a device model before startup.")
        return None
    for attempt in range(max(0, retries)):
        try:
            result = subprocess.run([adb, "devices"], capture_output=True, text=True, check=True, timeout=10)
            candidates = {parts[0] for line in result.stdout.splitlines()
                          if len(parts := line.strip().split()) >= 2 and parts[1] == "device"}
            if expected_serial:
                if expected_serial in candidates:
                    logger.info("Connected to explicitly selected device: %s", expected_serial)
                    return expected_serial
            else:
                matches = []
                for serial in sorted(candidates):
                    try:
                        model = subprocess.run(
                            [adb, "-s", serial, "shell", "getprop", "ro.product.model"],
                            capture_output=True, text=True, check=True, timeout=5,
                        ).stdout.strip()
                        if expected_model in model:
                            matches.append(serial)
                    except (OSError, subprocess.SubprocessError) as exc:
                        logger.debug("Could not confirm device model: %s", type(exc).__name__)
                if len(matches) == 1:
                    logger.info("Connected to uniquely matching device: %s", matches[0])
                    return matches[0]
                if len(matches) > 1:
                    logger.error("Multiple matching devices; set LASTZ_DEVICE_SERIAL explicitly.")
                    return None
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning("Device discovery failed: %s", type(exc).__name__)
        if attempt + 1 < retries:
            time.sleep(delay)
    logger.warning("Selected device is unavailable or no unique model match exists; no fallback selected.")
    return None


def _adb_log_category(args):
    """Allowlisted operation names only; never include serials or command payloads."""
    if not args:
        return "ADB command"
    operation = args[0] if args[0] in {"shell", "exec-out", "get-state", "devices", "pull", "push", "connect", "disconnect", "forward", "reverse", "version"} else "command"
    tool = ""
    if operation in {"shell", "exec-out"} and len(args) > 1:
        candidate = str(args[1]).split()[0] if str(args[1]).split() else ""
        if candidate in {"input", "screencap", "getprop", "am", "cmd", "wm", "dumpsys", "pidof"}:
            tool = " " + candidate
    return "ADB " + operation + tool + " (arguments omitted)"


def adb_command(self, *args):
        """
        Run an arbitrary ADB sub-command for self.device_id and return the
        CompletedProcess result (or None on timeout / fatal error).

        The full command constructed is:
            adb -s <device_id> <args[0]> <args[1]> ...

        Common usage patterns in this bot:
            self.adb_command("shell", "input", "tap", "540", "960")
            self.adb_command("shell", "input", "keyevent", "3")
            self.adb_command("shell", "screencap", "-p", "/sdcard/screen.png")
            self.adb_command("pull", "/sdcard/screen.png", local_path)

        Returns
        -------
        subprocess.CompletedProcess or None
            None is returned on TimeoutExpired (10 s) or any unexpected
            exception.  Non-zero return codes are logged as warnings but do
            not raise.

        Raises
        ------
        SystemExit
            If `adb` cannot be found at all (FileNotFoundError).
        """
        ownership = getattr(self, "_phone_ownership", None)
        if getattr(self, "_phone_ownership_required", False) and ownership is None:
            raise RuntimeError("Phone ownership is unavailable; Python input stopped")
        if ownership is not None:
            ownership.assert_owned()
        self._perf_metrics['adb_commands'] += 1
        adb = context._resolve_adb() or "adb"
        cmd = [adb, "-s", self.device_id] + list(args)
        cmd_str = _adb_log_category(args)
        try:
            self.adb_logger.trace(f"Executing: {cmd_str}")
            result = (ownership.shell(args[1:]) if ownership is not None and args and args[0] == "shell"
                      else subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False))
            if result.returncode != 0:
                self.adb_logger.warning(f"Command failed with code {result.returncode}: {cmd_str}")
                if result.stderr:
                    self.adb_logger.debug("ADB stderr omitted (%d characters)", len(result.stderr))
                    stderr_l = result.stderr.lower()
                    if "device" in stderr_l and ("not found" in stderr_l or "offline" in stderr_l or "unauthorized" in stderr_l):
                        self._recover_adb_device(reason="adb_transport_unavailable")
            else:
                self.adb_logger.trace(f"Command successful: {cmd_str}")
            return result
        except FileNotFoundError:
            self.adb_logger.critical(
                "adb not found. Install Android platform-tools or set LASTZ_ADB_PATH."
            )
            sys.exit(1)
        except subprocess.TimeoutExpired:
            self.adb_logger.error(f"Command timed out: {cmd_str}")
            return None
        except Exception as e:
            self.adb_logger.error("ADB command failed: %s (%s)", cmd_str, type(e).__name__)
            return None


def adb_screenshot(self):
    """
    Capture the current phone screen and return it as a BGR OpenCV ndarray.

    Capture strategy
    ----------------
    Primary:  capture_device_screen() — `adb exec-out screencap -p` pipes PNG
              bytes directly to stdout; decoded in-memory with cv2.imdecode.
              Fastest method, no temporary files.
    Fallback: _adb_screencap_pull() — saves to /sdcard/screen.png on the
              device then pulls it to a local temp file.  Used if exec-out
              fails (e.g. older adb versions or permission issues).

    Throttling
    ----------
    If CONFIG["screenshot_min_interval_ms"] > 0 and the last screencap was
    taken less than that many ms ago, the cached frame is returned as a copy
    instead of issuing a new `adb exec-out` command.  This dramatically
    reduces ADB traffic when multiple template checks run back-to-back within
    a single cycle step.

    Returns
    -------
    numpy.ndarray or None
        BGR image of shape (height, width, 3), or None if both methods fail.
    """
    self._perf_metrics['screenshots'] += 1
    if not self._adb_transport_ready():
        return None
    self.ensure_device_awake_unlocked(where="adb_screenshot")
    min_ms = int(context.CONFIG.get("screenshot_min_interval_ms", 0) or 0)
    now_ms = int(time.time() * 1000)
    
    # IMPROVED: Add lock for thread safety (if bot is ever multi-threaded)
    # For now, just ensure atomic check-and-set
    if min_ms > 0 and self._last_screenshot is not None and (now_ms - self._last_screenshot_ts) < min_ms:
        self.adb_logger.trace(f"Screenshot throttled; reused last image ({now_ms - self._last_screenshot_ts}ms ago)")
        # ADDED: Return a copy to prevent accidental mutation
        return self._last_screenshot.copy()

    img = None
    self.adb_logger.trace(f"Capturing screenshot (device={self.device_id})")
    try:
        img = context.capture_device_screen(self.device_id)
        self.adb_logger.trace(f"Screenshot exec-out OK: shape={img.shape}")
    except Exception as e:
        self.adb_logger.warning(f"Fast screenshot failed: {e}. Falling back to sdcard pull method.")
        try:
            img = context._adb_screencap_pull(self)
            self.adb_logger.trace(f"Screenshot fallback OK: shape={img.shape}")
        except Exception as e2:
            self.adb_logger.error(f"Fallback screenshot also failed: {e2}")
            img = None

    # --- update cache ---
    if img is not None:
        self._record_screenshot_success()
        self._last_screenshot = img
        self._last_screenshot_ts = now_ms
    else:
        recovered = self._record_screenshot_failure("adb_screenshot_failed")
        if recovered:
            self.ensure_device_awake_unlocked(force=True, where="adb_screenshot_recovery")
            self.adb_logger.info("Retrying screenshot after ADB recovery.")
            try:
                img = context.capture_device_screen(self.device_id)
                self._record_screenshot_success()
                self._last_screenshot = img
                self._last_screenshot_ts = int(time.time() * 1000)
            except Exception as e:
                self.adb_logger.error(f"Screenshot retry after ADB recovery failed: {e}")
                img = None
    return img


def _is_usable_adb_candidate(path: Path) -> bool:
    if not path.is_file():
        return False
    if os.name != "nt" and not os.access(path, os.X_OK):
        return False
    return True


def _resolve_adb() -> str | None:
    configured = (os.environ.get("LASTZ_ADB_PATH") or os.environ.get("ADB_PATH") or "").strip()
    if configured:
        configured_path = Path(configured).expanduser()
        if configured_path.is_file() and context._is_usable_adb_candidate(configured_path):
            return str(configured_path.resolve())
        return shutil.which(configured)

    here = context.PROJECT_ROOT
    system_adb = shutil.which("adb")

    if os.name != "nt":
        if system_adb:
            return system_adb
        for candidate in (here / "scrcpy-linux" / "adb", here / "scrcpy" / "adb"):
            if context._is_usable_adb_candidate(candidate):
                return str(candidate)
        return None

    for candidate in (here / "scrcpy" / "adb.exe", here / "scrcpy" / "adb"):
        if context._is_usable_adb_candidate(candidate):
            return str(candidate)
    if system_adb:
        return system_adb
    return None


def _resolve_tesseract() -> str | None:
    configured = (
        os.environ.get("LASTZ_TESSERACT_PATH")
        or os.environ.get("TESSERACT_PATH")
        or ""
    ).strip()
    if configured:
        configured_path = Path(configured).expanduser()
        if configured_path.is_file():
            return str(configured_path.resolve())
        return shutil.which(configured)
    return shutil.which("tesseract")


def capture_device_screen(device: str | None = None):
    """
    Capture a screenshot from the Android device using `adb exec-out screencap -p`.

    This is the fastest capture method: screencap writes PNG bytes directly to
    stdout without touching the device’s filesystem, and they are decoded
    in-memory with cv2.imdecode.  No temporary files are created.

    Parameters
    ----------
    device : str, optional
        ADB device serial.  If None, adb operates on the single connected
        device (or raises an error if multiple are connected).

    Returns
    -------
    numpy.ndarray
        BGR image of shape (height, width, 3).

    Raises
    ------
    RuntimeError
        If adb is not found, screencap exits non-zero, or the PNG cannot be
        decoded (e.g. corrupt / incomplete data).
    """
    adb = context._resolve_adb()
    if not adb:
        raise RuntimeError(
            "adb not found; install Android platform-tools or set LASTZ_ADB_PATH"
        )
    cmd = [adb]
    if device:
        cmd += ["-s", device]
    cmd += ["exec-out", "screencap", "-p"]
    
    logger = logging.getLogger('adb')
    logger.trace(f"capture_device_screen cmd={cmd}")
    
    timeout_seconds = float(context.CONFIG.get("adb_screenshot_timeout_seconds", 12.0) or 12.0)
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        # subprocess.run terminates and reaps its direct child before raising,
        # so this cannot leave the single-threaded bot waiting forever on a
        # stale `adb exec-out screencap` process.
        raise RuntimeError(
            f"screencap exec-out timed out after {timeout_seconds:.1f}s"
        ) from exc

    if proc.returncode != 0:
        raise RuntimeError(f"screencap exec-out failed rc={proc.returncode} stderr={proc.stderr.decode(errors='ignore')[:200]}")
    data = np.frombuffer(proc.stdout, np.uint8)
    
    logger.trace(f"screencap bytes={len(proc.stdout)}")
    
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        # dump first bytes to help diagnose PNG decode issues
        head = proc.stdout[:16]
        raise RuntimeError(f"Failed to decode screenshot from adb (len={len(proc.stdout)} head={list(head)})")
    return img


def _adb_screencap_pull(self):
    """Fallback screenshot method: save to sdcard then pull to host."""
    remote = "/sdcard/screen.png"
    local = str(
        Path(tempfile.gettempdir())
        / f"lastz_screen_{self.device_id}_{int(time.time()*1000)}.png"
    )
    self.adb_logger.trace(f"screencap fallback remote={remote} local={local}")
    # Capture on device
    self.adb_command("shell", "screencap", "-p", remote)
    # Pull to host
    self.adb_command("pull", remote, local)
    # Decode
    img = cv2.imread(local, cv2.IMREAD_COLOR)
    # Cleanup local temp
    try:
        os.remove(local)
    except Exception:
        pass
    if img is None:
        raise RuntimeError("Failed to decode pulled screenshot")
    self.adb_logger.trace(f"screencap fallback read OK: exists={os.path.exists(local)}")
    return img


def check_requirements():
    """
    Preflight check: verify that `adb` and `tesseract` are available.

    Resolution order for `adb`:
      - LASTZ_ADB_PATH / ADB_PATH override.
      - Linux and macOS: system PATH, then bundled legacy candidates.
      - Windows: bundled adb.exe candidates, then system PATH.

    Resolution order for `tesseract`:
      1. LASTZ_TESSERACT_PATH / TESSERACT_PATH override.
      2. System PATH.

    If any required tool is missing, logs a CRITICAL message with host-specific
    installation guidance and calls sys.exit(1).
    """
    log = logging.getLogger('bot')
    missing = []
    # scrcpy removed; only require adb and tesseract
    if not context._resolve_adb():
        missing.append("android-tools-adb (adb)")
    tesseract = context._resolve_tesseract()
    if not tesseract:
        missing.append("tesseract-ocr")

    if missing:
        log.critical("Missing required tools: " + ", ".join(missing))
        if platform.system() == "Darwin":
            log.info("On macOS, install with: brew install android-platform-tools tesseract")
        elif platform.system() == "Linux":
            log.info("On Debian/Linux, install with:")
            log.info("  sudo apt-get update && sudo apt-get install -y android-tools-adb tesseract-ocr")
        else:
            log.info("Install Android platform-tools and Tesseract, or set LASTZ_ADB_PATH and LASTZ_TESSERACT_PATH.")
        sys.exit(1)

    pytesseract.pytesseract.tesseract_cmd = tesseract
    log.trace(f"check_requirements: adb={context._resolve_adb()} tesseract={tesseract}")


class AndroidMixin:
    def adb_tap(self, x: int, y: int):
        """
        Send a tap event to the device at pixel coordinates (x, y).

        CONFIG["click_offset"] optionally offsets the requested point in both
        axes. This does not establish protection against detection and can move
        a tap outside its intended control. Metadata-based helper actions use
        validated live geometry instead.
        """
        offset = context.CONFIG.get("click_offset", 0)
        rx = x + random.randint(-offset, offset)
        ry = y + random.randint(-offset, offset)
        self.adb_logger.debug(f"Tapping at ({rx},{ry})")
        self.adb_command("shell", "input", "tap", str(int(rx)), str(int(ry)))
        self._invalidate_screenshot()

    def adb_swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int):
        """
        Send a swipe gesture from (x1, y1) to (x2, y2) over `duration_ms` ms.

        Used to scroll lists (e.g. the building menu when searching for the
        bounty building, or the world-map gather search).
        """
        self.adb_logger.debug(f"Swiping ({x1},{y1}) -> ({x2},{y2}) in {duration_ms}ms")
        self.adb_command("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms))
        self._invalidate_screenshot()

    def adb_keyevent(self, keycode: int):
        """
        Inject an Android key event by numeric keycode.

        Common keycodes used by this bot:
          3   KEYCODE_HOME    — returns to the Android launcher
          111 KEYCODE_ESCAPE  — closes in-game dialogs / navigates back
          187 KEYCODE_APP_SWITCH  — opens the recent-apps overview
        """
        self.adb_logger.trace(f"Keyevent: {keycode}")
        self.adb_command("shell", "input", "keyevent", str(keycode))
        self._invalidate_screenshot()

    def _invalidate_screenshot(self) -> None:
        """Drop the cached frame after any input that can change the UI."""
        self._last_screenshot = None
        self._last_screenshot_ts = 0.0

    def _record_screenshot_success(self) -> None:
        if self._consecutive_screenshot_failures:
            self.adb_logger.info("Screenshot capture recovered after %d failure(s).", self._consecutive_screenshot_failures)
        self._consecutive_screenshot_failures = 0

    def _record_screenshot_failure(self, reason: str = "") -> bool:
        """
        Count screenshot failures and, after a short streak, probe only
        the already-selected device serial. Returns True when a recovery attempt changed state
        and the caller should retry the screenshot once.
        """
        self._consecutive_screenshot_failures += 1
        limit = int(context.CONFIG.get("adb_screenshot_failure_recovery_threshold", 3) or 3)
        if self._consecutive_screenshot_failures < limit:
            return False
        return self._recover_adb_device(reason=reason)

    def _recover_adb_device(self, reason: str = "") -> bool:
        now = time.time()
        min_interval = float(context.CONFIG.get("adb_recovery_min_interval_seconds", 15.0) or 15.0)
        if self._adb_recovering or now - self._last_adb_recovery_ts < min_interval:
            return False

        self._adb_recovering = True
        self._last_adb_recovery_ts = now
        try:
            self.adb_logger.warning(
                "ADB screenshot health check failed %d times. Probing selected device. reason=%s",
                self._consecutive_screenshot_failures,
                reason,
            )
            # Recovery belongs to the selected serial. Discovery may return a
            # different phone, so it must never be used to rebind this session.
            selected = self.device_id
            if not selected:
                self.adb_logger.error("ADB recovery has no selected device; stopped.")
                return False
            try:
                result = subprocess.run(
                    [context._resolve_adb() or "adb", "-s", selected, "get-state"],
                    capture_output=True, text=True, timeout=5, check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                self.adb_logger.warning("Selected ADB device recovery failed: %s", exc)
                return False
            if result.returncode != 0 or result.stdout.strip() != "device":
                self.adb_logger.warning("Selected ADB device remains unavailable; no fallback selected.")
                return False
            if self.device_id != selected:
                self.adb_logger.error("Selected ADB device changed during recovery; stopped.")
                return False
            self.adb_logger.info("ADB recovery confirmed selected device %s.", selected)
            self._invalidate_screenshot()
            self._consecutive_screenshot_failures = 0
            self._obs_event("adb_recovered", device=self.device_id, reason=reason)
            return True
        finally:
            self._adb_recovering = False

    def _adb_transport_ready(self) -> bool:
        """Bound USB probes and back off without restarting the process."""
        now = time.monotonic()
        if now < getattr(self, "_transport_probe_after", 0):
            return getattr(self, "_transport_connected", True)
        try:
            probe = subprocess.run([context._resolve_adb() or "adb", "-s", self.device_id, "get-state"],
                                   capture_output=True, text=True, timeout=3, check=False)
            ready = probe.returncode == 0 and probe.stdout.strip() == "device"
        except (OSError, subprocess.TimeoutExpired):
            ready = False
        was_ready = getattr(self, "_transport_connected", True)
        self._transport_connected = ready
        if ready:
            self._transport_failures = 0
            self._transport_probe_after = now + 30
            if not was_ready:
                self._invalidate_screenshot()
                self.adb_logger.info("USB connection recovered; resuming workflows.")
        else:
            self._transport_failures = getattr(self, "_transport_failures", 0) + 1
            delay = min(300, 15 * 2 ** min(self._transport_failures - 1, 5))
            self._transport_probe_after = now + delay
            self._invalidate_screenshot()
            self.adb_logger.warning("USB device unavailable; next probe in %ss (attempt %s).", delay, self._transport_failures)
        return ready

    def configure_device_power_policy(self) -> None:
        """Keep the phone awake while attached to USB and stretch screen timeout."""
        if self._device_power_policy_configured or not context.CONFIG.get("device_configure_stay_awake", True):
            return
        self.game_logger.info("Configuring device stay-awake policy for USB power.")
        self.adb_command("shell", "svc", "power", "stayon", "usb")
        timeout_ms = int(context.CONFIG.get("device_screen_timeout_ms", 1800000) or 1800000)
        self.adb_command("shell", "settings", "put", "system", "screen_off_timeout", str(timeout_ms))
        self._device_power_policy_configured = True

    def _read_device_state(self) -> dict:
        """Read Android power/keyguard state without taking a screenshot."""
        state = {
            "display_on": None,
            "wakefulness": "",
            "keyguard_showing": None,
            "keyguard_monitor_showing": None,
            "keyguard_secure": None,
            "keyguard_input_restricted": None,
            "keyguard_monitor_input_restricted": None,
            "screen_state": "",
            "interactive_state": "",
            "focus": "",
            "unlocked": False,
            "raw_ok": False,
        }

        power = self.adb_command("shell", "dumpsys", "power")
        if power is not None and power.stdout:
            text = power.stdout
            state["raw_ok"] = True
            m = re.search(r"Display Power:\s*state=(\w+)", text)
            if m:
                state["display_on"] = m.group(1).upper() == "ON"
            m = re.search(r"mWakefulness=(\w+)", text)
            if m:
                state["wakefulness"] = m.group(1)

        policy = self.adb_command("shell", "dumpsys", "window", "policy")
        if policy is not None and policy.stdout:
            text = policy.stdout
            state["raw_ok"] = True
            m = re.search(r"KeyguardServiceDelegate[\s\S]*?showing=(true|false)", text)
            if m:
                state["keyguard_showing"] = m.group(1) == "true"
            m = re.search(r"KeyguardServiceDelegate[\s\S]*?secure=(true|false)", text)
            if m:
                state["keyguard_secure"] = m.group(1) == "true"
            m = re.search(r"KeyguardServiceDelegate[\s\S]*?inputRestricted=(true|false)", text)
            if m:
                state["keyguard_input_restricted"] = m.group(1) == "true"
            m = re.search(r"KeyguardStateMonitor[\s\S]*?mIsShowing=(true|false)", text)
            if m:
                state["keyguard_monitor_showing"] = m.group(1) == "true"
            m = re.search(r"KeyguardStateMonitor[\s\S]*?mInputRestricted=(true|false)", text)
            if m:
                state["keyguard_monitor_input_restricted"] = m.group(1) == "true"
            m = re.search(r"screenState=(\S+)", text)
            if m:
                state["screen_state"] = m.group(1)
            m = re.search(r"interactiveState=(\S+)", text)
            if m:
                state["interactive_state"] = m.group(1)

        windows = self.adb_command("shell", "dumpsys", "window", "windows")
        if windows is not None and windows.stdout:
            text = windows.stdout
            state["raw_ok"] = True
            m = re.search(r"mCurrentFocus=([^\n]+)", text)
            if m:
                state["focus"] = m.group(1).strip()

        display_on = state["display_on"] is True or state["screen_state"] == "SCREEN_STATE_ON"
        if state["keyguard_monitor_showing"] is not None:
            keyguard_showing = state["keyguard_monitor_showing"]
        else:
            keyguard_showing = state["keyguard_showing"]
        keyguard_clear = keyguard_showing is False
        state["unlocked"] = bool(display_on and keyguard_clear)
        return state

    def _send_pin_keyevents(self) -> None:
        """Send the configured numeric PIN via Android keyevents. Never log it."""
        pin = str(context.CONFIG.get("device_pin", "") or "")
        digit_to_keycode = {str(i): str(7 + i) for i in range(10)}
        keycodes = [digit_to_keycode[d] for d in pin if d in digit_to_keycode]
        if not keycodes:
            self.game_logger.warning("Device PIN is not configured; cannot unlock secure keyguard.")
            return
        keycodes.append("66")  # ENTER
        self.adb_command("shell", "input", "keyevent", *keycodes)
        self._invalidate_screenshot()

    def ensure_device_awake_unlocked(self, force: bool = False, where: str = "") -> bool:
        """
        Recover the Android device from screen-off, lock screen, or PIN screen.
        Uses dumpsys state as the primary signal and the proven OnePlus flow:
        MENU wakes, swipe exposes PIN, digit keyevents submit the PIN.
        """
        if not context.CONFIG.get("device_auto_heal_enabled", True):
            return True
        if self._device_heal_in_progress:
            return True

        now = time.time()
        interval = float(context.CONFIG.get("device_heal_check_interval_seconds", 20.0) or 20.0)
        if not force and now - self._last_device_heal_check_ts < interval:
            return True
        self._last_device_heal_check_ts = now

        self._device_heal_in_progress = True
        try:
            self.configure_device_power_policy()
            state = self._read_device_state()
            self.game_logger.debug(
                "Device state at %s: display_on=%s keyguard=%s monitor_keyguard=%s restricted=%s monitor_restricted=%s focus=%s",
                where,
                state.get("display_on"),
                state.get("keyguard_showing"),
                state.get("keyguard_monitor_showing"),
                state.get("keyguard_input_restricted"),
                state.get("keyguard_monitor_input_restricted"),
                state.get("focus"),
            )
            if state.get("unlocked"):
                return True

            max_attempts = int(context.CONFIG.get("device_unlock_max_attempts", 3) or 3)
            sx1, sy1, sx2, sy2, sdur = context.CONFIG.get("device_unlock_swipe", (540, 1850, 540, 420, 350))
            for attempt in range(1, max_attempts + 1):
                self.game_logger.warning(
                    "Device needs unlock/heal at %s; attempt %d/%d.",
                    where or "unknown",
                    attempt,
                    max_attempts,
                )
                self._obs_event("device_heal_attempt", where=where, attempt=attempt, max_attempts=max_attempts)

                state = self._read_device_state()
                if state.get("unlocked"):
                    self._obs_event("device_heal_end", where=where, status="already_unlocked")
                    return True

                if state.get("display_on") is not True:
                    self.adb_command("shell", "input", "keyevent", "82")  # MENU wakes this OnePlus reliably.
                    self._invalidate_screenshot()
                    time.sleep(float(context.CONFIG.get("device_wake_delay_seconds", 0.8) or 0.8))

                state = self._read_device_state()
                if state.get("unlocked"):
                    self._obs_event("device_heal_end", where=where, status="unlocked_after_wake")
                    return True

                self.adb_command("shell", "input", "swipe", str(sx1), str(sy1), str(sx2), str(sy2), str(sdur))
                self._invalidate_screenshot()
                time.sleep(float(context.CONFIG.get("device_swipe_delay_seconds", 0.45) or 0.45))
                self._send_pin_keyevents()
                time.sleep(float(context.CONFIG.get("device_pin_delay_seconds", 1.0) or 1.0))

                state = self._read_device_state()
                if state.get("unlocked"):
                    self.game_logger.info("Device unlocked successfully at %s.", where or "unknown")
                    self._obs_event("device_heal_end", where=where, status="ok", attempt=attempt)
                    return True

            self.game_logger.error("Device auto-heal failed at %s.", where or "unknown")
            self._obs_event("device_heal_end", where=where, status="failed")
            return False
        finally:
            self._device_heal_in_progress = False
