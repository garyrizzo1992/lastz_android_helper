"""Navigation services extracted from the application facade."""
import cv2
import numpy as np
import time
from bot.context import context


def confirm_screen(self, must: list[str] | None = None, any_of: list[str] | None = None,
                   none_of: list[str] | None = None, timeout: float = 2.5, poll: float = 0.2,
                   where: str | None = None, recover: bool = False, abort_on_fail: bool = False,
                   must_screen: list[str] | str | None = None,
                   any_screen: list[str] | str | None = None,
                   none_screen: list[str] | str | None = None) -> bool:
        """
        Assert the current screen state by template visibility rules.

        Polls the screen every `poll` seconds until `timeout` expires,
        re-checking the conditions on each fresh screenshot.  Returns True
        as soon as all conditions are satisfied simultaneously.

        Conditions (all evaluated per screenshot)
        ------------------------------------------
        must     All named templates must be visible at the same time.
        any_of   At least one of these templates must be visible.
        none_of  None of these templates may be visible.
        must_screen  All named screen sanity checks must pass.
        any_screen   At least one named screen sanity check must pass.
        none_screen  None of these screen sanity checks may pass.

        Usage examples
        --------------
        # Confirm we're on the base/home screen:
        confirm_screen(must=["home"], timeout=3.0, where="after close")

        # Confirm we've left the home screen (world map opened):
        confirm_screen(none_of=["home"], timeout=2.0)

        # Either trucks or truck chest must appear:
        confirm_screen(any_of=["truck", "truck_chest"], timeout=5.0)

        Parameters
        ----------
        must, any_of, none_of : list[str], optional
            Template name lists.  None / empty list means “no constraint”.
        timeout : float
            Maximum seconds to keep polling before returning False.
        poll : float
            Interval in seconds between screenshot polls.
        where : str, optional
            Human-readable label included in log messages to aid debugging.
        recover : bool
            If True and the check fails, call ensure_base_view() to attempt
            recovery before returning False.
        abort_on_fail : bool
            If True and the check fails, set self._abort_cycle = True so that
            run_one_cycle() can detect and restart the cycle cleanly.

        Returns
        -------
        bool
            True if all conditions were met within timeout, else False.
        """
        end = time.time() + max(0.0, timeout)
        must = must or []
        any_of = any_of or []
        none_of = none_of or []
        def _screen_list(value):
            if value is None:
                return []
            if isinstance(value, str):
                return [value]
            return list(value)
        must_screen = _screen_list(must_screen)
        any_screen = _screen_list(any_screen)
        none_screen = _screen_list(none_screen)
        self._obs_event(
            "confirm_screen_start",
            where=where or "",
            must=must,
            any_of=any_of,
            none_of=none_of,
            must_screen=must_screen,
            any_screen=any_screen,
            none_screen=none_screen,
            timeout=timeout,
        )

        def ok_now() -> bool:
            img = self.adb_screenshot()
            if img is None:
                return False
            # must all present
            for t in must:
                if self.find_template(t, img, click=False) is None:
                    return False
            # any_of at least one present (if provided)
            if any_of:
                if not any(self.find_template(t, img, click=False) for t in any_of):
                    return False
            # none_of all absent
            for t in none_of:
                if self.find_template(t, img, click=False):
                    return False
            for s in must_screen:
                if not self.is_screen(s, img):
                    return False
            if any_screen:
                if not any(self.is_screen(s, img) for s in any_screen):
                    return False
            for s in none_screen:
                if self.is_screen(s, img):
                    return False
            return True

        while time.time() < end:
            if ok_now():
                if where:
                    self.game_logger.debug(f"confirm_screen OK at '{where}'")
                self._obs_event("confirm_screen_ok", where=where or "")
                return True
            time.sleep(poll)

        msg_where = f" at {where}" if where else ""
        self.game_logger.warning(
            "confirm_screen FAILED%s: must=%s any_of=%s none_of=%s must_screen=%s any_screen=%s none_screen=%s",
            msg_where,
            must,
            any_of,
            none_of,
            must_screen,
            any_screen,
            none_screen,
        )
        fail_img = self.adb_screenshot()
        status = {"must": {}, "any_of": {}, "none_of": {}, "must_screen": {}, "any_screen": {}, "none_screen": {}}
        if fail_img is not None:
            for t in must:
                status["must"][t] = self.find_template(t, fail_img, click=False) is not None
            for t in any_of:
                status["any_of"][t] = self.find_template(t, fail_img, click=False) is not None
            for t in none_of:
                status["none_of"][t] = self.find_template(t, fail_img, click=False) is not None
            for s in must_screen:
                status["must_screen"][s] = self.is_screen(s, fail_img)
            for s in any_screen:
                status["any_screen"][s] = self.is_screen(s, fail_img)
            for s in none_screen:
                status["none_screen"][s] = self.is_screen(s, fail_img)
            self._obs_capture(f"confirm_failed_{where or 'unknown'}", image=fail_img, where=where or "")
        self._obs_event(
            "confirm_screen_failed",
            where=where or "",
            must=must,
            any_of=any_of,
            none_of=none_of,
            must_screen=must_screen,
            any_screen=any_screen,
            none_screen=none_screen,
            status=status,
            abort_on_fail=abort_on_fail,
            recover=recover,
        )
        if abort_on_fail:
            self._abort_cycle = True
            self.game_logger.warning(f"Abort flag set due to confirm_screen failure{msg_where}.")
        if recover:
            self.ensure_base_view()
        return False


def dismiss_navigation_blocker(self, img: np.ndarray | None) -> str | None:
    """Dismiss one known global overlay and return its stable blocker name."""
    if img is None:
        return None

    blocker = None
    if context._is_alliance_speedup_reward_dialog(img):
        blocker = "alliance_speedup_reward"
        self.game_logger.info("Alliance speedup reward detected; clicking Confirm.")
        self.adb_tap(*context.CONFIG["action_coords"]["healing_reward_confirm"])

    if blocker is None:
        hx1, hy1, hx2, hy2 = context.CONFIG.get(
            "hero_progression_roi", (0, 40, 650, 210)
        )
        if self.find_template(
            "hero_progression", img[hy1:hy2, hx1:hx2], click=False
        ) is not None:
            blocker = "hero_progression"
            self.game_logger.info(
                "Hero Progression event detected; dismissing it with Back."
            )
            self.adb_keyevent(4)

    if blocker is None:
        x1, y1, x2, y2 = context.CONFIG.get(
            "endless_night_close_roi", (875, 270, 990, 380)
        )
        event_close_loc = self.find_template(
            "endless_night_close", img[y1:y2, x1:x2], click=False
        )
        if event_close_loc is not None:
            event_close_screen_loc = (
                x1 + event_close_loc[0],
                y1 + event_close_loc[1],
            )
            if self._endless_night_close_backdrop_visible(
                img, event_close_screen_loc
            ):
                template = self.templates["endless_night_close"]
                close_x = event_close_screen_loc[0] + template.shape[1] // 2
                close_y = event_close_screen_loc[1] + template.shape[0] // 2
                blocker = "endless_night"
                self.game_logger.info(
                    "Endless Night event detected; clicking close at (%d, %d).",
                    close_x,
                    close_y,
                )
                self.adb_tap(close_x, close_y)

    if blocker is None and self.find_template("quit_game", img, click=False):
        blocker = "quit_game"
        self.game_logger.info("Quit dialog detected; dismissing it.")
        self.adb_tap(777, 1270)

    if blocker is None:
        radial_roi = img[1000:1400, 250:850]
        stale_builder_radial = None
        if context._locate_green_builder_upgrade(img) is not None:
            stale_builder_radial = ("green_upgrade_control", 1.0)
        for template_name, match_threshold in (
            ("builder_upgrade_menu", 0.86),
            ("builder_upgrade_menu_glow", 0.70),
        ):
            if stale_builder_radial is not None:
                break
            template = self.templates.get(template_name)
            if template is None:
                continue
            template_bgr = template[:, :, :3] if template.ndim == 3 else template
            if (
                radial_roi.shape[0] < template_bgr.shape[0]
                or radial_roi.shape[1] < template_bgr.shape[1]
            ):
                continue
            result = cv2.matchTemplate(
                radial_roi, template_bgr, cv2.TM_CCOEFF_NORMED
            )
            _, score, _, _ = cv2.minMaxLoc(result)
            if score >= match_threshold:
                stale_builder_radial = (template_name, score)
                break
        if stale_builder_radial is not None:
            blocker = "construction_radial"
            self.game_logger.info(
                "Stale construction radial detected (%s score=%.3f); dismissing it.",
                stale_builder_radial[0],
                stale_builder_radial[1],
            )
            self.adb_keyevent(111)

    if blocker is not None:
        self._obs_event("navigation_blocker_dismissed", blocker=blocker)
    return blocker


def ensure_base_view(
    self,
    timeout: float | None = None,
    max_esc: int = 6,
) -> bool:
    """Recover and positively confirm the base screen.

    Recovery is state-driven: one known global blocker is dismissed per
    frame, known panels use their own back control, world view uses the base
    toggle, and ESC is reserved for unknown states.  Base confirmation combines
    stable HUD regions; a recently observed animated home marker remains
    supporting evidence but is not required once the HUD is unambiguous.

    ``timeout`` defaults to ``base_recovery_timeout_seconds``.  ``max_esc`` is
    a safety budget, not a completion condition; after it is exhausted the
    method keeps observing the UI until the wall-clock timeout.
    """
    self.game_logger.info("Ensuring base view...")
    if timeout is None:
        timeout = float(context.CONFIG.get("base_recovery_timeout_seconds", 30.0))
    deadline = time.monotonic() + max(1.0, float(timeout))
    poll_seconds = float(context.CONFIG.get("base_recovery_poll_seconds", 0.35))
    stability_seconds = float(context.CONFIG.get("base_stability_seconds", 1.5))
    marker_grace_seconds = float(context.CONFIG.get("base_marker_grace_seconds", 8.0))
    min_sanity_matches = int(context.CONFIG.get("base_min_sanity_matches", 2))
    esc_count = 0
    iter_no = 0

    img = None
    home_stable_since = None
    home_marker_seen_at = None
    max_esc_warned = False
    hq_templates = ("hq", "hq2")
    back_button_screens = {"chat", "mail", "radar", "trucks"}
    panel_back_attempts: dict[str, int] = {}
    while time.monotonic() < deadline:
        iter_no += 1
        self.game_logger.debug(
            "ensure_base_view: iter=%d esc_count=%d/%d",
            iter_no,
            esc_count,
            max_esc,
        )

        img = self.adb_screenshot()
        if img is None:
            time.sleep(context.CONFIG["timing"]["fast_click_delay"])
            continue

        blocker = self.dismiss_navigation_blocker(img)
        if blocker is not None:
            home_stable_since = None
            home_marker_seen_at = None
            time.sleep(context.CONFIG["timing"]["action_delay"])
            continue

        detected = self.detect_screen(img, candidates=("home", "world", "chat", "mail", "radar", "trucks"))
        screen_name = detected.get("screen")
        self.game_logger.debug(
            "ensure_base_view screen=%s score=%.3f matches=%s",
            screen_name or "unknown",
            detected.get("score", -1.0),
            detected.get("matches", 0),
        )

        home_loc = self.find_template("home", img, click=False)
        now = time.monotonic()
        if home_loc is not None:
            home_marker_seen_at = now
        evidence = context._base_recovery_evidence(
            detected,
            home_marker_visible=home_loc is not None,
            home_marker_seen_at=home_marker_seen_at,
            now=now,
            min_sanity_matches=min_sanity_matches,
            marker_grace_seconds=marker_grace_seconds,
        )
        if evidence["candidate"]:
            if home_stable_since is None:
                home_stable_since = now
                self.game_logger.info(
                    "Base candidate detected (HUD matches=%d score=%.3f); "
                    "confirming stability for %.1fs.",
                    evidence["matches"],
                    evidence["score"],
                    stability_seconds,
                )
            elif now - home_stable_since >= stability_seconds:
                self.game_logger.info(
                    "Stable base view confirmed (HUD matches=%d marker_recent=%s).",
                    evidence["matches"],
                    evidence["marker_recent"],
                )
                return True
            time.sleep(poll_seconds)
            continue
        home_stable_since = None

        if screen_name in back_button_screens:
            panel_back_attempts[screen_name] = panel_back_attempts.get(screen_name, 0) + 1
            home_marker_seen_at = None
            if panel_back_attempts[screen_name] == 1:
                self.game_logger.info(
                    "%s screen detected; tapping its back button.", screen_name
                )
                self.adb_tap(76, 1988)
            elif esc_count < max_esc:
                self.game_logger.info(
                    "%s screen persisted after its back button; pressing Android Back.",
                    screen_name,
                )
                self.adb_keyevent(111)
                esc_count += 1
            else:
                time.sleep(poll_seconds)
                continue
            time.sleep(context.CONFIG["timing"]["action_delay"])
            continue

        loc_hq = None
        for tpl in hq_templates:
            loc_hq = self.find_template(tpl, img, click=True)
            if loc_hq:
                home_marker_seen_at = None
                self.game_logger.info("%s detected; clicked to return to base.", tpl.upper())
                time.sleep(context.CONFIG["timing"]["action_delay"])
                break
        if loc_hq:
            continue

        # Event overlays retain parts of the normal HUD and used to satisfy
        # the permissive one-ROI world check.  Require two independent world
        # ROIs before tapping the bottom-right base/world toggle.
        world_check = next(
            (check for check in detected.get("checks", []) if check.get("screen") == "world"),
            {},
        )
        confident_world = bool(
            screen_name == "world"
            and world_check.get("ok")
            and int(world_check.get("matches", 0)) >= 2
        )
        if confident_world:
            self.game_logger.info(
                "World view confidently detected (matches=%s score=%.3f); tapping Base toggle.",
                world_check.get("matches", 0),
                world_check.get("score", -1.0),
            )
            home_marker_seen_at = None
            self.adb_tap(*context.CONFIG["action_coords"]["open_world"])
            time.sleep(context.CONFIG["timing"]["action_delay"])
            continue

        if esc_count < max_esc:
            self.game_logger.debug("Unknown screen while ensuring base; pressing ESC.")
            home_marker_seen_at = None
            self.adb_keyevent(111)
            esc_count += 1
            time.sleep(context.CONFIG["timing"]["fast_click_delay"])
        else:
            if not max_esc_warned:
                self.game_logger.warning(
                    "Max ESC attempts reached (%d). Waiting for UI to stabilize...",
                    max_esc,
                )
                max_esc_warned = True
            time.sleep(poll_seconds)

    last_home_debug = self._template_debug.get("home", {})
    final_screen = self.detect_screen(
        img,
        candidates=("home", "world", "chat", "mail", "radar", "trucks"),
    ) if img is not None else {}
    self._obs_capture("ensure_base_view_timeout", image=img)
    self.game_logger.warning(
        "ensure_base_view: timed out after %.1fs; final_screen=%s score=%.3f "
        "matches=%s home_sqdiff=%s home_ccoef=%s esc=%d",
        float(timeout),
        final_screen.get("screen") or "unknown",
        final_screen.get("score", -1.0),
        final_screen.get("matches", 0),
        last_home_debug.get("sqdiff"),
        last_home_debug.get("ccoef"),
        esc_count,
    )
    return False


def close_all_apps(self):
        """
        Clear the Android recent-apps list and return to the home screen.

        Sequence (up to 3 attempts)
        ---------------------------
        1. Press KEYCODE_APP_SWITCH (187) to open the recent-apps overview.
        2. Tap the “Clear All” button at CONFIG["action_coords"]["clear_all"].
        3. Press KEYCODE_HOME (3) twice to ensure the launcher is shown.

        Called at startup (to clear leftover state from a previous run) and
        between game-slot rotations (to fully close one game before opening
        the next).  Falls back to go_home() if all attempts fail.

        Returns
        -------
        bool
            True if clear succeeded, False if all attempts failed (go_home
            fallback is still called).
        """
        self.ensure_device_awake_unlocked(force=True, where="close_all_apps")
        self.game_logger.info("Closing all recent applications.")
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                self.game_logger.debug(f"Attempt {attempt + 1} to close all apps...")
                
                # Press the recent apps button
                self.adb_keyevent(187)  # KEYCODE_APP_SWITCH
                time.sleep(context.CONFIG["timing"]["action_delay"] + 1)  # Extra time for animation
                
                # Tap the 'Clear All' button using hardcoded coordinates
                self.adb_tap(*context.CONFIG["action_coords"]["clear_all"])
                time.sleep(context.CONFIG["timing"]["action_delay"] + 1)  # Extra time for clearing
                
                # Press home to ensure we're back to launcher
                self.adb_keyevent(3)  # KEYCODE_HOME
                time.sleep(context.CONFIG["timing"]["action_delay"])
                
                # Verify we're at home by pressing home again
                self.adb_keyevent(3)  # KEYCODE_HOME
                time.sleep(context.CONFIG["timing"]["action_delay"])
                
                self.game_logger.info(f"Successfully closed all apps on attempt {attempt + 1}.")
                return True
                
            except Exception as e:
                self.game_logger.warning(f"Attempt {attempt + 1} failed to close apps: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)  # Wait before retry
                else:
                    self.game_logger.error("All attempts to close apps failed.")
                    
        # Fallback: just go home
        self.game_logger.info("Falling back to home screen.")
        self.go_home()
        return False


def go_home(self):
    """Press the Android HOME button (keycode 3) and wait for the launcher."""
    self.ensure_device_awake_unlocked(force=True, where="go_home")
    self.adb_keyevent(3)  # KEYCODE_HOME
    time.sleep(context.CONFIG["timing"]["action_delay"])


def launch_game(self, game_name: str):
    """
    Switch focus to a specific game slot.

    Sequence
    --------
    1. Press HOME to return to the Android launcher.
    2. Tap the home-screen icon for `game_name` at CONFIG["game_coords"][game_name].
    3. Wait 15 seconds for the game app to load and render.
    4. Call ensure_base_view() to safely dismiss overlays and confirm that the
       in-game base screen is showing.

    Parameters
    ----------
    game_name : str
        Key into CONFIG["game_coords"], e.g. "game1" through "game4".

    Returns
    -------
    bool
        True on success, False if game_name is not in CONFIG["game_coords"].
    """
    coord = context.CONFIG["game_coords"].get(game_name)
    if not coord:
        self.game_logger.error(f"No coordinates configured for '{game_name}'")
        return False
    self.game_logger.info(f"Launching {game_name} at {coord}")
    if not self.ensure_device_awake_unlocked(force=True, where=f"launch_game:{game_name}"):
        return False
    self.go_home()
    time.sleep(context.CONFIG["timing"]["fast_click_delay"])
    self.adb_tap(coord[0], coord[1])
    self.game_logger.info(f"Waiting 15s for {game_name} to load...")
    time.sleep(15)
    # Never blind-tap after launch: event splash screens can put destructive
    # actions at otherwise harmless coordinates.  Recovery inputs are chosen
    # only after inspecting the current frame in ensure_base_view().
    ok = self.ensure_base_view(timeout=30.0, max_esc=10)
    if not ok:
        self.game_logger.warning(f"{game_name} launched but base view was not confirmed.")
    return ok


class NavigationMixin:
    def _note_stuck(self, game_name: str, reason: str, threshold: int | None = None) -> bool:
        """Return True when the same per-game failure has repeated often enough to escalate."""
        threshold = threshold or int(context.CONFIG.get("stuck_recovery_threshold", 3) or 3)
        key = f"{game_name}:{reason}"
        self._stuck_counts[key] = self._stuck_counts.get(key, 0) + 1
        count = self._stuck_counts[key]
        self.game_logger.warning("[%s] stuck marker '%s' count=%d/%d", game_name, reason, count, threshold)
        self._obs_event("stuck_marker", game=game_name, reason=reason, count=count, threshold=threshold)
        return count >= threshold

    def _reset_stuck(self, game_name: str, reason: str | None = None) -> None:
        prefix = f"{game_name}:"
        for key in list(self._stuck_counts):
            if key.startswith(prefix) and (reason is None or key == f"{game_name}:{reason}"):
                self._stuck_counts.pop(key, None)

    def recover_current_game(self, game_name: str, reason: str) -> bool:
        """Heavy recovery path used after repeated same-state failures."""
        self.game_logger.warning("[%s] escalating recovery: %s", game_name, reason)
        self._obs_event("game_recovery_start", game=game_name, reason=reason)
        try:
            self.close_all_apps()
            time.sleep(context.CONFIG["timing"]["action_delay"])
            ok = bool(self.launch_game(game_name))
            self._obs_event("game_recovery_end", game=game_name, reason=reason, status="ok" if ok else "failed")
            if ok:
                self._reset_stuck(game_name)
            return ok
        except Exception as e:
            self.game_logger.error("[%s] recovery failed: %s", game_name, e, exc_info=True)
            self._obs_event("game_recovery_end", game=game_name, reason=reason, status="error", error=str(e))
            return False

    def tap_then_confirm(self, name: str, tap_func, *, must=None, any_of=None, none_of=None,
                         timeout: float = 2.5, retries: int = 2, recover: bool = False,
                         abort_on_fail: bool = False, must_screen=None,
                         any_screen=None, none_screen=None) -> bool:
        """
        Run a tap action and require the expected screen state afterwards.
        Centralising this pattern keeps state-changing UI steps from silently
        continuing after a missed tap or stale screen.
        """
        attempts = max(1, int(retries))
        for attempt in range(1, attempts + 1):
            self.game_logger.debug("tap_then_confirm %s attempt %d/%d", name, attempt, attempts)
            tap_func()
            time.sleep(context.CONFIG["timing"]["action_delay"])
            if self.confirm_screen(
                must=must,
                any_of=any_of,
                none_of=none_of,
                must_screen=must_screen,
                any_screen=any_screen,
                none_screen=none_screen,
                timeout=timeout,
                where=f"{name} attempt {attempt}",
                abort_on_fail=False,
            ):
                self._obs_event("tap_then_confirm_ok", name=name, attempt=attempt)
                return True
        self.game_logger.warning("tap_then_confirm failed: %s", name)
        self._obs_event("tap_then_confirm_failed", name=name, attempts=attempts)
        if abort_on_fail:
            self._abort_cycle = True
        if recover:
            self.ensure_base_view()
        return False
