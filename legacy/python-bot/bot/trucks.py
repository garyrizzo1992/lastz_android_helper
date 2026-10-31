"""Trucks services extracted from the application facade."""
import cv2
import numpy as np
import time
import random
import os
import json
import pytesseract
import re
from bot.context import context


def do_trucks(self, game_name):
    """
    Collect completed trade trucks and dispatch new ones for `game_name`.

    Per-game daily cooldown
    -----------------------
    Truck trades reset once per day at CONFIG["daily_reset_hour"] (04:00).
    When all trades are exhausted, a cooldown timestamp is stored in
    self.trucks_cooldown_until_by_game[game_name] and persisted to
    logs/trucks_state.json.  This function returns early (None) when
    now < cooldown_until.  The cooldown is checked by run_one_cycle() before
    this function is even called.

    Opening the Truck UI
    --------------------
    1. ensure_base_view().
    2. Wait up to 3 s for the "truck" template then tap it to open the
       Truck building panel.
    3. Tap (792, 2070) up to 3 times until either the "truck_chest"
       template or the green plus button is visible — confirms the UI is
       open.

    OCR trade count
    ---------------
    Reads CONFIG["truck_trade_counter_roi"] using extract_text_from_roi().
    Parses text of the form "X/Y" (used / total) to compute trades_left.
    If OCR fails and CONFIG["trucks_require_ocr"] is True (default), the
    function returns None without touching the cooldown.  If False, falls
    back to CONFIG["trucks_default_trades_when_unknown"] (default 2).

    Main loop (up to 10 iterations)
    --------------------------------
    Each iteration:
      a. Take a screenshot.
      b. If "truck_chest" is visible, tap it (collect a completed truck),
         wait long_delay, then press ESC twice to dismiss reward popups.
      c. Else if trades_left > 0, locate the green plus button via
         _locate_truck_plus() and tap it to open dispatch dialog. Refresh one
         truck at a time until purple/orange is found, then tap Go to send it.
      d. Break when neither action is possible (no chest, no plus button).

    Cooldown after exhaustion
    -------------------------
    When trades_left reaches 0, _next_daily_reset_ts() is called and the
    result is saved to trucks_cooldown_until_by_game and persisted to disk.

    Cleanup
    -------
    The `finally` block always presses ESC twice and calls ensure_base_view()
    to ensure the truck UI is dismissed regardless of how the function exits.

    Parameters
    ----------
    game_name : str
        Key into CONFIG["game_coords"] (e.g. "game1").  Used for per-game
        cooldown tracking and logging.

    Returns
    -------
    int or None
        Number of trades remaining after processing, 0 if exhausted, or
        None on open failure / OCR failure (if trucks_require_ocr is True).
    """
    self.game_logger.info(f"Performing truck actions for {game_name}: Collect resources and send.")
    self._obs_event("trucks_start", game=game_name)
    if self._daily_action_complete(game_name, "trucks"):
        self.game_logger.info("[%s] Trucks already completed for the current Malta day.", game_name)
        return 0
    try:
        if not self.ensure_base_view():
            self.game_logger.warning(f"[{game_name}] Base view not confirmed before trucks; aborting trucks.")
            self._obs_event("trucks_end", game=game_name, status="base_not_confirmed")
            self._record_action(game_name, "trucks", "failed", "Base view was not confirmed")
            return None

        if not self.wait_for_template("truck", timeout=3.0, click=True):
            for _ in range(2):
                img = self.adb_screenshot()
                if img is not None and self.find_template("truck", img, click=True):
                    break
                time.sleep(context.CONFIG["timing"]["fast_click_delay"])
            else:
                self.game_logger.warning("Failed to open Truck UI after retries.")
                self._obs_capture(f"trucks_open_failed_{game_name}", game=game_name)
                self._obs_event("trucks_end", game=game_name, status="open_failed")
                self._record_action(game_name, "trucks", "failed", "Truck UI did not open")
                return None

        truck_ui_visible = False
        for _ in range(3):
            img = self.adb_screenshot()
            if img is not None and (
                self.is_screen("trucks", img)
                or self.find_template("truck_chest", img, click=False)
                or self._locate_truck_plus(img)
            ):
                truck_ui_visible = True
                break
            trade_point = context._find_ocr_word_center(
                img,
                "trade",
                tuple(context.CONFIG.get("truck_open_trade_roi", (450, 1750, 1050, 2140))),
            )
            if trade_point is not None:
                self.game_logger.info(
                    "[%s] Opening truck trade page via OCR at (%d, %d).",
                    game_name,
                    trade_point[0],
                    trade_point[1],
                )
                self.adb_tap(*trade_point)
            else:
                self.adb_tap(x=792, y=2070)
            time.sleep(context.CONFIG["timing"]["fast_click_delay"])
        if not truck_ui_visible:
            self.game_logger.warning(f"[{game_name}] Truck UI not confirmed after 3 taps; aborting trucks.")
            self._obs_capture(f"trucks_ui_not_visible_{game_name}", game=game_name)
            self._obs_event("trucks_end", game=game_name, status="ui_not_visible")
            self._record_action(game_name, "trucks", "failed", "Truck page was not confirmed")
            return None

        trades_left = None
        trades_unknown = False
        try:
            ROI_X1, ROI_Y1, ROI_X2, ROI_Y2 = context.CONFIG.get(
                "truck_trade_counter_roi", (80, 35, 580, 125)
            )
            trade_text = self.extract_text_from_roi(
                x1=ROI_X1,
                y1=ROI_Y1,
                x2=ROI_X2,
                y2=ROI_Y2,
                device=self.device_id,
                psm="6",
                whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:/' ",
                save_debug=True,
            )
            self.game_logger.trace(f"[{game_name}] Truck OCR normalized='{trade_text}'")
            counter = context._parse_fraction(trade_text)
            if counter:
                used, total = counter
                trades_left = max(0, total - used)
                self.game_logger.info(f"[{game_name}] Truck trades parsed: used={used}, total={total}, trades_left={trades_left}")
            else:
                self.game_logger.warning(f"[{game_name}] Truck trade count OCR did not parse from normalized text: '{trade_text}'")
        except Exception as e:
            self.game_logger.warning(f"[{game_name}] OCR for truck trade count failed: {e}")

        if context.CONFIG.get("trucks_require_ocr", True) and trades_left is None:
            self.game_logger.info(f"[{game_name}] Trade count unknown (OCR failed). Will not dispatch; no cooldown set.")
            self._obs_capture(f"trucks_ocr_unknown_{game_name}", game=game_name)
            self._obs_event("trucks_end", game=game_name, status="ocr_unknown")
            self._record_action(game_name, "trucks", "failed", "Daily trade counter OCR failed")
            return None
        if trades_left is None:
            trades_left = max(1, int(context.CONFIG.get("trucks_default_trades_when_unknown", 1)))
            trades_unknown = True
            self.game_logger.info(f"[{game_name}] Trade count unknown; assuming {trades_left} available (will adjust on the fly).")

        if trades_left == 0:
            cooldown_ts = context._next_daily_reset_ts()
            self.trucks_cooldown_until_by_game[game_name] = cooldown_ts
            self._save_trucks_state()
            secs = int(cooldown_ts - time.time())
            self.game_logger.info(f"[{game_name}] No truck trades left. Cooldown set for {secs}s until next reset.")
            self._obs_event("trucks_end", game=game_name, status="cooldown_set", trades_left=0, cooldown_secs=secs)
            self._mark_daily_action_complete(
                game_name,
                "trucks",
                "Daily truck trades exhausted",
                used=used,
                total=total,
                trades_left=0,
            )
            return 0

        collected_any = False
        dispatched_count = 0
        max_iters = 10
        for _ in range(max_iters):
            img = self.adb_screenshot()
            if img is None:
                self.game_logger.warning("Screenshot is None during truck loop. Breaking.")
                break
            if self.find_template("truck_chest", img, click=True):
                collected_any = True
                self.game_logger.info("Collected a completed truck via template match.")
                time.sleep(context.CONFIG["timing"]["long_delay"])
                for _ in range(2):
                    self.adb_keyevent(111)
                    time.sleep(context.CONFIG["timing"]["long_delay"])
                continue

            if trades_left > 0:
                img = self.adb_screenshot()
                plus_target = self._locate_truck_plus(img)
                if plus_target:
                    self.adb_tap(*plus_target)
                    self.game_logger.info(f"Preparing a truck dispatch (plus at {plus_target}).")
                    time.sleep(context.CONFIG["timing"]["long_delay"])
                    target_grade = self._refresh_truck_until_target(game_name)
                    if target_grade is None:
                        break
                    self.game_logger.info(
                        "[%s] Dispatching %s truck.", game_name, target_grade
                    )
                    self.adb_tap(x=532, y=1764)
                    time.sleep(context.CONFIG["timing"]["long_delay"])
                    trades_left -= 1
                    dispatched_count += 1
                    self.game_logger.info(f"Trades left after dispatch: {trades_left}")
                    continue

            break
        else:
            self.game_logger.warning(f"[{game_name}] Reached max truck loop iterations ({max_iters}); exiting trucks processing.")

        if trades_left == 0 and not trades_unknown:
            cooldown_ts = context._next_daily_reset_ts()
            self.trucks_cooldown_until_by_game[game_name] = cooldown_ts
            self._save_trucks_state()
            secs = int(cooldown_ts - time.time())
            self.game_logger.info(f"[{game_name}] Trades exhausted during processing. Cooldown set for {secs}s until next reset.")
            self._mark_daily_action_complete(
                game_name,
                "trucks",
                "Daily truck trades dispatched",
                used=total,
                total=total,
                trades_left=0,
                dispatched=dispatched_count,
                collected=collected_any,
            )
        elif dispatched_count or collected_any:
            self._record_action(
                game_name,
                "trucks",
                "success",
                "Truck processing made progress",
                trades_left=trades_left,
                dispatched=dispatched_count,
                collected=collected_any,
            )
        else:
            self._record_action(
                game_name,
                "trucks",
                "unavailable",
                "No dispatchable target truck was available",
                trades_left=trades_left,
            )

        self._obs_event(
            "trucks_end",
            game=game_name,
            status="ok",
            trades_left=trades_left,
            collected_any=collected_any,
            trades_unknown=trades_unknown,
        )
        return trades_left

    except Exception as e:
        self.game_logger.error(f"[{game_name}] Truck handling failed: {e}", exc_info=True)
        self._obs_capture(f"trucks_exception_{game_name}", game=game_name, error=str(e))
        self._obs_event("trucks_end", game=game_name, status="error", error=str(e))
        self._record_action(game_name, "trucks", "failed", str(e))
        return None
    finally:
        self.adb_keyevent(111)
        time.sleep(context.CONFIG["timing"]["action_delay"])
        self.adb_keyevent(111)
        time.sleep(context.CONFIG["timing"]["action_delay"])
        self.ensure_base_view()


def do_truck_plunder(self, game_name: str | None = None) -> bool:
    """Dynamically inspect visible trucks and fight only weaker opponents."""
    game_label = game_name or "unknown"
    if not context.CONFIG.get("truck_plunder_enabled", False):
        return False
    if not self.ensure_base_view():
        return False

    self.game_logger.info("Scanning visible opponent trucks for safe plunder targets.")
    self.adb_tap(*context.CONFIG["action_coords"]["truck_plunder_entry"])
    time.sleep(context.CONFIG["timing"]["action_delay"])

    cards = list(context.CONFIG.get("truck_plunder_first_five_cards", []))

    def card_is_selected(frame: np.ndarray | None, card: tuple[int, int]) -> bool:
        if frame is None:
            return False
        x, y = card
        patch = frame[max(0, y - 115):min(frame.shape[0], y + 10), max(0, x - 80):min(frame.shape[1], x + 80)]
        if patch.size == 0:
            return False
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        return cv2.countNonZero(cv2.inRange(hsv, (35, 90, 100), (95, 255, 255))) >= 100

    def selected_card_count(frame: np.ndarray | None) -> int:
        return sum(1 for card in cards if card_is_selected(frame, card))

    def ensure_first_five() -> tuple[bool, np.ndarray | None]:
        frame = self.adb_screenshot()
        for card in cards:
            if not card_is_selected(frame, card):
                self.adb_tap(*card)
                time.sleep(context.CONFIG["timing"]["fast_click_delay"])
                frame = self.adb_screenshot()
        return selected_card_count(frame) == len(cards) == 5, frame

    def read_power(roi: tuple[int, int, int, int]) -> tuple[float | None, str]:
        text = self.extract_text_from_roi(
            *roi,
            psm="7",
            whitelist="0123456789.,KMB",
        )
        return context._parse_power_value(text), text

    def read_detail_power() -> tuple[float | None, str]:
        """Read the full numeric power shown on the pre-Loot detail card."""
        frame = self.adb_screenshot()
        if frame is None:
            return None, ""
        x1, y1, x2, y2 = context.CONFIG["truck_plunder_opponent_power_roi"]
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None, ""
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        enlarged = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        _, binary = cv2.threshold(enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        text = pytesseract.image_to_string(
            binary,
            config="--psm 7 -c tessedit_char_whitelist=0123456789,",
        ).strip()
        digits = re.sub(r"\D", "", text)
        # Truck power is displayed as a seven-to-ten digit integer.  Anything
        # else is a non-target/decorative truck or an unreadable panel.
        if not 7 <= len(digits) <= 10:
            return None, text
        return float(int(digits)), text

    cache_ttl = float(context.CONFIG.get("truck_plunder_power_cache_ttl", 21600))
    cached_entry = self._truck_plunder_power_cache.get(game_label)
    cached_hero_power = None
    if cached_entry and time.monotonic() - cached_entry[1] <= cache_ttl:
        cached_hero_power = cached_entry[0]
        self.game_logger.info(
            "Using cached first-five hero power for %s: %.2fM.",
            game_label,
            cached_hero_power / 1_000_000,
        )
    elif cached_entry:
        self._truck_plunder_power_cache.pop(game_label, None)

    targets = list(context.CONFIG.get("truck_plunder_target_points", []))
    random.shuffle(targets)
    max_targets = int(context.CONFIG.get("truck_plunder_max_targets", 3))

    try:
        for target_index, target in enumerate(targets[:max_targets], start=1):
            self.game_logger.info("Inspecting randomized truck target %d/%d at %s.", target_index, min(max_targets, len(targets)), target)
            self.adb_tap(*target)
            time.sleep(context.CONFIG["timing"]["action_delay"])

            opponent_power, opponent_text = read_detail_power()
            if opponent_power is None:
                self.game_logger.warning("Truck target %d skipped: opponent power OCR was inconclusive (%r).", target_index, opponent_text)
                self.adb_tap(*context.CONFIG["action_coords"]["truck_plunder_panel_dismiss"])
                time.sleep(context.CONFIG["timing"]["fast_click_delay"])
                continue

            # Inspection is deliberately limited to the truck's detail panel.
            # A missing cache is not a reason to press Loot: that would open the
            # hero selector for every candidate and defeats the pre-check.
            if cached_hero_power is None:
                self.game_logger.info(
                    "Truck target %d skipped: no current first-five power cache; "
                    "leaving the detail panel without opening Loot.",
                    target_index,
                )
                self.adb_tap(*context.CONFIG["action_coords"]["truck_plunder_panel_dismiss"])
                time.sleep(context.CONFIG["timing"]["fast_click_delay"])
                continue

            required_ratio = float(context.CONFIG.get("truck_plunder_min_power_ratio", 1.05))
            self.game_logger.info(
                "Truck target %d power check: cached heroes=%.2fM opponent=%.2fM (need %.2fx).",
                target_index,
                cached_hero_power / 1_000_000,
                opponent_power / 1_000_000,
                required_ratio,
            )
            if cached_hero_power < opponent_power * required_ratio:
                self.game_logger.info("Truck target %d skipped from matchup screen: opponent is too strong.", target_index)
                self.adb_tap(*context.CONFIG["action_coords"]["truck_plunder_panel_dismiss"])
                time.sleep(context.CONFIG["timing"]["fast_click_delay"])
                continue

            # Only an attackable target pays the cost of touching the hero
            # selector.  Reconfirm the lineup and power immediately before Fight.
            self.adb_tap(*context.CONFIG["action_coords"]["truck_plunder_loot"])
            time.sleep(context.CONFIG["timing"]["action_delay"])
            lineup_ok, _ = ensure_first_five()
            current_power, current_text = read_power(context.CONFIG["truck_plunder_our_power_roi"])
            if not lineup_ok or current_power is None:
                self.game_logger.warning("Truck target %d skipped: final lineup/power verification failed (%r).", target_index, current_text)
                self.adb_tap(*context.CONFIG["action_coords"]["truck_plunder_back"])
                time.sleep(context.CONFIG["timing"]["fast_click_delay"])
                continue
            verified_power = min(cached_hero_power, current_power)
            self._truck_plunder_power_cache[game_label] = (verified_power, time.monotonic())
            if verified_power < opponent_power * required_ratio:
                self.game_logger.info("Truck target %d skipped after final power verification.", target_index)
                self.adb_tap(*context.CONFIG["action_coords"]["truck_plunder_back"])
                time.sleep(context.CONFIG["timing"]["fast_click_delay"])
                continue

            self.game_logger.info("Truck target %d is safely weaker; starting plunder.", target_index)
            self.adb_tap(*context.CONFIG["action_coords"]["truck_plunder_fight"])
            time.sleep(context.CONFIG["timing"]["long_delay"])
            self._record_action(game_label, "truck_plunder", "success", "Safe truck plunder started", our_power=verified_power, opponent_power=opponent_power)
            return True
    finally:
        self.ensure_base_view()

    self._record_action(game_label, "truck_plunder", "unavailable", "No safely weaker visible truck")
    return False


class TrucksMixin:
    def _trucks_state_path(self) -> str:
        # Keep under logs_dir to survive restarts
        return os.path.join(context.CONFIG.get("logs_dir", "logs"), "trucks_state.json")

    def _load_trucks_state(self) -> None:
        path = self._trucks_state_path()
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                now = time.time()
                # Keep only future cooldowns; coerce keys/values
                cleaned = {}
                for k, v in (data.items() if isinstance(data, dict) else []):
                    try:
                        ts = float(v)
                        if ts > now:
                            cleaned[str(k)] = ts
                    except Exception:
                        continue
                self.trucks_cooldown_until_by_game.update(cleaned)
                if cleaned:
                    self.game_logger.info(f"Loaded trucks cooldowns: { {k:int(v-now) for k,v in cleaned.items()} }s remaining")
        except Exception as e:
            self.game_logger.debug(f"Failed to load trucks state: {e}")

    def _save_trucks_state(self) -> None:
        path = self._trucks_state_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            now = time.time()
            to_save = {k: float(v) for k, v in self.trucks_cooldown_until_by_game.items() if v and v > now}
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(to_save, f, separators=(",", ":"))
            os.replace(tmp, path)
        except Exception as e:
            self.game_logger.debug(f"Failed to save trucks state: {e}")
            # ADDED: Clean up temp file if it exists
            try:
                tmp = path + ".tmp"
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass

    def _locate_truck_plus(self, screenshot: np.ndarray | None = None) -> tuple[int, int] | None:
        """
        Find the green "+" dispatch button inside the Truck building UI.

        Uses colour-blob detection (_locate_by_color) configured from
        CONFIG["truck_plus_color"].  The green hue is distinct enough from the
        game's other UI elements to reliably identify the button without a
        template image.

        Returns (cx, cy) in full-screen pixel coordinates, or None if the
        button is not visible (no trades remain, or UI is not open).
        """
        return self._locate_by_color(self._truck_plus_color, screenshot)

    def _detect_truck_grade(self, screenshot: np.ndarray | None = None) -> tuple[str, dict[str, float]]:
        """Classify the dispatch truck by the saturated colour of its body."""
        img = screenshot if screenshot is not None else self.adb_screenshot()
        cfg = context.CONFIG.get("truck_grade_refresh", {})
        if img is None:
            return "unknown", {"purple": 0.0, "orange": 0.0}

        x1, y1, x2, y2 = cfg.get("grade_roi", (150, 350, 920, 820))
        roi = img[y1:y2, x1:x2]
        if roi.size == 0:
            return "unknown", {"purple": 0.0, "orange": 0.0}

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        purple = cv2.inRange(hsv, np.array([135, 90, 90]), np.array([179, 255, 255]))
        orange = cv2.inRange(hsv, np.array([5, 120, 100]), np.array([35, 255, 255]))
        area = float(purple.size)
        scores = {
            "purple": float(np.count_nonzero(purple)) / area,
            "orange": float(np.count_nonzero(orange)) / area,
        }
        min_ratio = float(cfg.get("target_min_ratio", 0.10))
        if scores["purple"] >= min_ratio:
            return "purple", scores
        if scores["orange"] >= min_ratio:
            return "orange", scores
        return "other", scores

    def _truck_high_grade_warning_visible(self, screenshot: np.ndarray | None = None) -> bool:
        """Detect the Confirm/Cancel warning shown when refreshing a high-grade truck."""
        img = screenshot if screenshot is not None else self.adb_screenshot()
        if img is None:
            return False
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        confirm = hsv[1080:1230, 100:500]
        cancel = hsv[1080:1230, 520:905]
        if confirm.size == 0 or cancel.size == 0:
            return False
        orange = cv2.inRange(confirm, np.array([5, 100, 100]), np.array([35, 255, 255]))
        blue = cv2.inRange(cancel, np.array([85, 80, 80]), np.array([130, 255, 255]))
        return (
            np.count_nonzero(orange) / float(orange.size) >= 0.20
            and np.count_nonzero(blue) / float(blue.size) >= 0.20
        )

    def _read_truck_refresh_tickets(self, screenshot: np.ndarray | None = None) -> tuple[int, int] | None:
        """Read the visible refresh-ticket balance and per-refresh cost."""
        img = screenshot if screenshot is not None else self.adb_screenshot()
        if img is None:
            return None
        x1, y1, x2, y2 = context.CONFIG.get("truck_grade_refresh", {}).get(
            "ticket_roi", (780, 800, 990, 1030)
        )
        roi = img[y1:y2, x1:x2]
        if roi.size == 0:
            return None
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        for candidate in (gray, binary, cv2.bitwise_not(binary)):
            try:
                text = pytesseract.image_to_string(
                    candidate,
                    config="--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789/",
                )
            except Exception:
                continue
            match = re.search(r"(\d+)\s*/\s*(\d+)", text or "")
            if match:
                return int(match.group(1)), int(match.group(2))
        return None

    def _refresh_truck_until_target(self, game_name: str) -> str | None:
        """Spend refresh tickets one at a time until a purple or orange truck appears."""
        cfg = context.CONFIG.get("truck_grade_refresh", {})
        max_refreshes = max(0, int(cfg.get("max_refreshes", 50)))
        refresh_x, refresh_y = cfg.get("refresh_button", (887, 1050))
        cancel_x, cancel_y = cfg.get("warning_cancel", (715, 1165))
        delay = float(cfg.get("refresh_delay", context.CONFIG["timing"]["action_delay"]))

        for refresh_count in range(max_refreshes + 1):
            img = self.adb_screenshot()
            grade, scores = self._detect_truck_grade(img)
            self.game_logger.info(
                "[%s] Truck grade scan: grade=%s purple=%.3f orange=%.3f refreshes=%d",
                game_name,
                grade,
                scores["purple"],
                scores["orange"],
                refresh_count,
            )
            if grade in {"purple", "orange"}:
                self._obs_event(
                    "truck_target_grade_found",
                    game=game_name,
                    grade=grade,
                    refreshes=refresh_count,
                    **scores,
                )
                return grade

            if self._truck_high_grade_warning_visible(img):
                self.game_logger.warning(
                    "[%s] High-grade refresh warning detected; cancelling to preserve the truck.",
                    game_name,
                )
                self.adb_tap(cancel_x, cancel_y)
                time.sleep(delay)
                return "high_quality"

            if refresh_count >= max_refreshes:
                break
            tickets = self._read_truck_refresh_tickets(img)
            if tickets is not None:
                available, cost = tickets
                if cost <= 0 or available < cost:
                    self.game_logger.warning(
                        "[%s] Truck refresh tickets exhausted (%d/%d); stopping safely.",
                        game_name,
                        available,
                        cost,
                    )
                    return None
            elif refresh_count > 0:
                self.game_logger.warning(
                    "[%s] Truck refresh ticket count is unreadable; stopping to avoid premium-currency spending.",
                    game_name,
                )
                return None
            self.adb_tap(refresh_x, refresh_y)
            time.sleep(delay)

        self.game_logger.warning(
            "[%s] No purple or orange truck found after %d refreshes; not dispatching a lower grade.",
            game_name,
            max_refreshes,
        )
        self._obs_event(
            "truck_target_grade_not_found",
            game=game_name,
            max_refreshes=max_refreshes,
        )
        return None
