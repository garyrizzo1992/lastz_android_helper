"""Radar services extracted from the application facade."""
import cv2
import numpy as np
import time
import os
import datetime
import re
from bot.context import context


def _save_treasure_screenshot(self, game_name: str | None = None, frame: np.ndarray | None = None) -> str | None:
        """Save a treasure screenshot and return the local file path."""
        img = frame if frame is not None else self.adb_screenshot()
        if img is None:
            return None
        out_dir = context.CONFIG.get("treasure_screenshot_dir") or os.path.join(context.CONFIG.get("debug_dir", "debug"), "treasures")
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception:
            return None
        safe_game = re.sub(r"[^A-Za-z0-9_.-]+", "_", game_name or "unknown")
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(out_dir, f"treasure_{safe_game}_{stamp}.png")
        if cv2.imwrite(path, img):
            return path
        return None


def _report_radar_treasure(self, game_name: str | None = None) -> bool:
        """Find treasure icon in radar view, then notify Discord and attach a screenshot when possible."""
        if not bool(context.CONFIG.get("treasure_alert_enabled", True)):
            return False

        screenshot = self.adb_screenshot()
        if screenshot is None:
            return False

        loc = self.find_template("treasure", screenshot, click=False)
        if not loc:
            return False

        cooldown = float(context.CONFIG.get("treasure_alert_cooldown_seconds", 180.0) or 0.0)
        now = time.time()
        if (now - float(getattr(self, "_last_treasure_alert_ts", 0.0))) < cooldown:
            self.game_logger.info("Treasure detected on radar (cooldown active).")
            return True

        webhook = (
            (context.CONFIG.get("discord_treasures_webhook") or "").strip()
            or (os.environ.get("DISCORD_TREASURES_WEBHOOK_URL") or "").strip()
            or (context.CONFIG.get("discord_webhook") or "").strip()
            or (os.environ.get("DISCORD_WEBHOOK_URL") or "").strip()
        )

        if not webhook:
            if not getattr(self, "_treasure_missing_webhook_warned", False):
                self.game_logger.warning(
                    "Treasure detected but no webhook is configured. Set discord_treasures_webhook or DISCORD_TREASURES_WEBHOOK_URL."
                )
                self._treasure_missing_webhook_warned = True
            return True

        game_label = game_name or "unknown"
        self.game_logger.info("Treasure detected on radar for %s at (%d, %d)", game_label, loc[0], loc[1])

        clicked = bool(self.find_template("treasure", screenshot, click=True))
        post_click_frame = self.adb_screenshot()
        shot_path = self._save_treasure_screenshot(game_label, frame=post_click_frame)

        if clicked and not self.is_visible("radar_check", timeout=0.0):
            self.adb_command("shell", "input", "keyevent", "4")
            time.sleep(context.CONFIG["timing"]["action_delay"])

        msg = f"[Treasure] Radar treasure found for {game_label}."
        if clicked:
            msg += " Clicked treasure."
        else:
            msg += " Could not click treasure reliably."

        sent = False
        if shot_path and os.path.exists(shot_path):
            try:
                with open(shot_path, "rb") as f:
                    sent = context._discord_webhook_post(
                        content=msg,
                        webhook_url=webhook,
                        timeout=float(context.CONFIG.get("discord_timeout", 4.0)),
                        file_bytes=f.read(),
                        file_name=os.path.basename(shot_path),
                    )
            except Exception:
                sent = False

        if not sent:
            sent = context._discord_webhook_post(
                content=msg,
                webhook_url=webhook,
                timeout=float(context.CONFIG.get("discord_timeout", 4.0)),
            )

        if sent:
            self.game_logger.info("Treasure alert sent to Discord for %s", game_label)
            self._last_treasure_alert_ts = now
        else:
            self.game_logger.warning("Failed to send treasure alert to Discord for %s", game_label)
        return True


def process_radar_events(self, game_name: str | None = None) -> int:
    """
    Dispatch healthy troops to human-head and pickaxe radar tasks.

    Radar tasks run before normal gathering so an available march is not
    consumed by a long resource gather first.  A dispatch is allowed only
    when the world sidebar confirms a free march and the march dialog reports
    a selected Troop Capacity greater than zero.
    """
    cfg = context.CONFIG.get("radar_events", {})
    game_label = game_name or "unknown"
    if not cfg.get("enabled", False):
        return 0

    def open_radar() -> np.ndarray | None:
        if not self.ensure_base_view():
            return None
        base_frame = self.adb_screenshot()
        if not self.find_template("radar", base_frame, click=True):
            return None
        time.sleep(context.CONFIG["timing"]["long_delay"])
        radar_frame = self.adb_screenshot()
        if radar_frame is None or not self.is_screen("radar", radar_frame):
            self.game_logger.warning("[%s] Radar event screen did not open.", game_label)
            return None
        return radar_frame

    def candidates(frame: np.ndarray) -> list[tuple[str, int, int, float, dict]]:
        found: list[tuple[str, int, int, float, dict]] = []
        roi = tuple(cfg.get("marker_roi", (250, 450, 900, 1350)))
        for event_cfg in cfg.get("events", ()):
            template = self.templates.get(event_cfg.get("template", ""))
            if template is None:
                continue
            for x, y, score in context._template_match_centers(
                frame,
                template,
                roi,
                threshold=float(event_cfg.get("threshold", 0.85)),
                max_matches=int(cfg.get("max_events_per_check", 4)),
            ):
                found.append((str(event_cfg.get("kind", "unknown")), x, y, score, event_cfg))
        # Prefer the short pickaxe contests, then the head/HQ attack.
        priority = {"pickaxe": 0, "head": 1}
        found.sort(key=lambda item: (priority.get(item[0], 9), -item[3]))
        return found

    dispatched = 0
    saw_candidate = False
    radar_frame = open_radar()
    if radar_frame is None:
        self._record_action(game_label, "radar_events", "unavailable", "Radar was not available")
        self.ensure_base_view()
        return 0

    max_events = max(1, int(cfg.get("max_events_per_check", 4)))
    for _ in range(max_events):
        available = candidates(radar_frame)
        if not available:
            break
        saw_candidate = True
        kind, marker_x, marker_y, score, event_cfg = available[0]
        self.game_logger.info(
            "[%s] Opening %s radar event at (%d, %d), score %.3f.",
            game_label,
            kind,
            marker_x,
            marker_y,
            score,
        )
        self.adb_tap(marker_x, marker_y)
        time.sleep(context.CONFIG["timing"]["action_delay"])
        detail_frame = self.adb_screenshot()
        detail_text = context._ocr_frame_text(
            detail_frame,
            tuple(cfg.get("detail_text_roi", (200, 1550, 1000, 1900))),
            psm=11,
        ).lower()
        keywords = tuple(str(word).lower() for word in event_cfg.get("detail_keywords", ()))
        if keywords and not any(word in detail_text for word in keywords):
            self.game_logger.warning(
                "[%s] %s marker detail was not confirmed by OCR; proceeding from the marker match: %r",
                game_label,
                kind,
                detail_text[:180],
            )
            self._obs_capture(
                f"radar_event_detail_unconfirmed_{game_label}_{kind}",
                image=detail_frame,
                game=game_label,
                event_kind=kind,
            )
            if bool(cfg.get("require_detail_ocr", False)):
                break

        self.adb_tap(*tuple(cfg.get("go_button", (540, 2045))))
        time.sleep(float(cfg.get("post_go_delay", 2.5)))
        target_frame = self.adb_screenshot()
        before_status = self.read_march_status(
            target_frame,
            where=f"radar {kind} before attack",
        )
        if before_status is None or self.march_slots_full(before_status):
            reason = "march status unknown" if before_status is None else "all march slots busy"
            self.game_logger.info("[%s] Skipping %s radar event: %s.", game_label, kind, reason)
            self._record_action(
                game_label,
                "radar_events",
                "unavailable",
                f"{kind} event skipped: {reason}",
            )
            break

        attack_point = context._find_ocr_word_center(
            target_frame,
            "attack",
            tuple(cfg.get("attack_word_roi", (300, 1100, 800, 1700))),
        )
        if attack_point is None:
            attack_point = tuple(cfg.get("attack_fallback", (540, 1450)))
        self.adb_tap(*attack_point)
        time.sleep(float(cfg.get("post_attack_delay", 1.5)))
        dispatch_frame = self.adb_screenshot()

        capacity = context._ocr_troop_capacity(
            dispatch_frame,
            tuple(context.CONFIG.get("troop_capacity_value_rois", ())),
        )
        if capacity is None:
            self.game_logger.warning(
                "[%s] Skipping %s radar event because Troop Capacity could not be read.",
                game_label,
                kind,
            )
            self._record_action(
                game_label,
                "radar_events",
                "unavailable",
                f"{kind} event skipped: Troop Capacity OCR failed",
            )
            self._obs_capture(
                f"radar_event_capacity_unknown_{game_label}_{kind}",
                image=dispatch_frame,
                game=game_label,
                event_kind=kind,
            )
            break
        selected, maximum = capacity
        if selected <= 0:
            self.game_logger.info(
                "[%s] Skipping %s radar event: Troop Capacity is %d/%d; healthy trained troops are required.",
                game_label,
                kind,
                selected,
                maximum,
            )
            self._record_action(
                game_label,
                "radar_events",
                "unavailable",
                f"{kind} event skipped: no healthy trained troops selected",
                selected=selected,
                maximum=maximum,
            )
            break

        march_point = context._find_ocr_word_center(
            dispatch_frame,
            "march",
            tuple(cfg.get("march_word_roi", (250, 1350, 750, 1700))),
        )
        if march_point is None:
            march_buttons = context._locate_green_rect_buttons(
                dispatch_frame,
                tuple(cfg.get("march_button_roi", (250, 1350, 750, 1750))),
                min_width=int(cfg.get("march_button_min_width", 250)),
                max_width=int(cfg.get("march_button_max_width", 520)),
                min_height=int(cfg.get("march_button_min_height", 65)),
                max_height=int(cfg.get("march_button_max_height", 180)),
            )
            if not march_buttons:
                march_buttons = context._locate_green_rect_buttons(
                    dispatch_frame,
                    tuple(cfg.get("march_button_roi", (250, 1350, 750, 1750))),
                    min_width=int(cfg.get("march_button_min_width", 250)),
                    max_width=int(cfg.get("march_button_max_width", 520)),
                    min_height=int(cfg.get("march_button_min_height", 65)),
                    max_height=int(cfg.get("march_button_max_height", 180)),
                    hsv_lower=(90, 70, 70), hsv_upper=(130, 255, 255),
                )
            if march_buttons:
                march_point = march_buttons[-1]
                self.game_logger.info(
                    "[%s] %s radar March label OCR failed; using scoped button fallback at (%d, %d).",
                    game_label,
                    kind,
                    march_point[0],
                    march_point[1],
                )
            else:
                self.game_logger.warning("[%s] %s radar March button was not found.", game_label, kind)
                self._obs_capture(
                    f"radar_event_march_missing_{game_label}_{kind}",
                    image=dispatch_frame,
                    game=game_label,
                    event_kind=kind,
                )
                break

        self.adb_tap(*march_point)
        time.sleep(float(cfg.get("post_march_delay", 2.0)))
        after_frame = self.adb_screenshot()
        after_status = self.read_march_status(
            after_frame,
            where=f"radar {kind} after march",
        )
        confirmed, reason = self.march_dispatch_confirmed(before_status, after_status)
        if not confirmed:
            self.game_logger.warning(
                "[%s] %s radar dispatch was not confirmed: %s.",
                game_label,
                kind,
                reason,
            )
            self._record_action(
                game_label,
                "radar_events",
                "failed",
                f"{kind} dispatch not confirmed",
                reason=reason,
                selected=selected,
                maximum=maximum,
            )
            self._obs_capture(
                f"radar_event_dispatch_unconfirmed_{game_label}_{kind}",
                image=after_frame,
                game=game_label,
                event_kind=kind,
                reason=reason,
            )
            break

        dispatched += 1
        self.game_logger.info(
            "[%s] %s radar dispatch confirmed with Troop Capacity %d/%d (%s).",
            game_label,
            kind,
            selected,
            maximum,
            reason,
        )
        self._record_action(
            game_label,
            "radar_events",
            "success",
            f"{kind} radar event dispatched",
            selected=selected,
            maximum=maximum,
            confirmation=reason,
        )
        if self.march_slots_full(after_status):
            break
        radar_frame = open_radar()
        if radar_frame is None:
            break

    self.ensure_base_view()
    if dispatched == 0 and not saw_candidate:
        self._record_action(
            game_label,
            "radar_events",
            "unavailable",
            "No dispatchable human-head or pickaxe radar event",
        )
    return dispatched


def do_radar(self, game_name: str | None = None):
        """
        Clear the radar building’s detected-enemy list.

        Opens the radar panel (taps the "radar" template), navigates to the
    radar check sub-tab, scans for treasure icons, then taps "Clear All"
    up to 5 times to dismiss entries.  Each iteration calls
    confirm_screen(must=["radar_check"]) to abort early if the panel
    unexpectedly closes.

        Returns
        -------
        bool
            True if the radar was not visible (nothing to do) or all clears
            completed successfully.  False if confirm_screen reported an abort.
        """
        game_label = game_name or "unknown"
        if self.find_template("radar", self.adb_screenshot(), click=True):
            self.game_logger.info("Radar opened.")
            time.sleep(context.CONFIG["timing"]["long_delay"])
            self.adb_tap(x=108, y=428)
            time.sleep(context.CONFIG["timing"]["action_delay"])
            self._report_radar_treasure(game_name=game_name)
            for _ in range(5):
                if not self.confirm_screen(must=["radar_check"], must_screen="radar", timeout=2.0, where="radar before clear", abort_on_fail=True):
                    self._record_action(game_label, "radar", "failed", "Radar screen was lost during clear")
                    return False
                self._report_radar_treasure(game_name=game_name)
                self.adb_tap(*context.CONFIG["action_coords"]["radar_clear_all"])
                time.sleep(context.CONFIG["timing"]["action_delay"])
            self._record_action(game_label, "radar", "success", "Radar entries cleared")
        else:
            self._record_action(game_label, "radar", "unavailable", "No radar action available")
        return True
