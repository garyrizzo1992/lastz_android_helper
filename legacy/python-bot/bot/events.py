"""Events services extracted from the application facade."""
import time
from bot.context import context


def do_boomer_auto_join(self, game_name: str | None = None) -> bool:
    """Enable or renew Danger Lurks (Boomer) Auto Team-Up for one account."""
    cfg = context.CONFIG.get("boomer_auto_join", {})
    game_label = game_name or "unknown"
    if not cfg.get("enabled", False):
        return False
    if not self.ensure_base_view():
        self._record_action(game_label, "boomer_auto_join", "failed", "Base view unavailable")
        return False

    self.game_logger.info("[%s] Renewing Danger Lurks Boomer Auto Team-Up.", game_label)
    self.adb_tap(*tuple(cfg.get("event_center", context.CONFIG["action_coords"]["event_center"])))
    time.sleep(float(cfg.get("post_event_center_delay", 2.5)))
    frame = self.adb_screenshot()
    danger_roi = tuple(cfg.get("danger_lurks_roi", (500, 1850, 1060, 2160)))
    danger_page_open = context._ocr_title_matches(
        context._ocr_frame_text(
            frame,
            tuple(cfg.get("danger_page_title_roi", (0, 30, 500, 150))),
            psm=11,
        ),
        "Danger Lurks",
    )
    if danger_page_open:
        self.game_logger.info("[%s] Danger Lurks event is already open.", game_label)

    def locate_danger_lurks(current_frame):
        ocr_point = context._find_ocr_phrase_center(current_frame, "danger lurks", danger_roi)
        if ocr_point is not None:
            return ocr_point
        portrait_match = context._locate_boomer_event_card(
            current_frame,
            self.templates.get("boomer_event"),
            tuple(cfg.get("boomer_portrait_roi", (0, 1850, 1080, 2160))),
            float(cfg.get("boomer_portrait_scale", 0.75)),
            float(cfg.get("boomer_portrait_threshold", 0.82)),
        )
        if portrait_match is None:
            return None
        x, y, score = portrait_match
        self.game_logger.info(
            "[%s] Found Danger Lurks via Boomer portrait at (%d, %d), score %.3f.",
            game_label,
            x,
            y,
            score,
        )
        return x, y

    danger_point = None if danger_page_open else locate_danger_lurks(frame)
    carousel_swipe = tuple(cfg.get("carousel_swipe", (820, 2020, 520, 2020)))
    carousel_reverse_swipe = tuple(
        cfg.get("carousel_reverse_swipe", (520, 2020, 820, 2020))
    )
    max_swipes = max(0, int(cfg.get("carousel_max_swipes", 8)))
    # Usually one leftward swipe exposes Danger Lurks.  If the Event Center
    # remembers a position to its right, sweep back in the opposite direction
    # as well rather than repeatedly pushing against the carousel edge.
    scan_swipes = [carousel_swipe] * max_swipes + [carousel_reverse_swipe] * (max_swipes * 2)
    for swipe in (() if danger_page_open else scan_swipes):
        if danger_point is not None:
            break
        self.adb_swipe(*swipe, duration_ms=450)
        time.sleep(float(cfg.get("post_carousel_delay", 1.0)))
        frame = self.adb_screenshot()
        danger_point = locate_danger_lurks(frame)
    if danger_point is None and not danger_page_open:
        self.game_logger.warning("[%s] Danger Lurks was not found in Event Center.", game_label)
        self._record_action(game_label, "boomer_auto_join", "unavailable", "Danger Lurks event was not found")
        self._obs_capture("danger_lurks_event_missing", image=frame, game=game_label)
        self.ensure_base_view()
        return False

    if not danger_page_open:
        self.adb_tap(*danger_point)
        time.sleep(float(cfg.get("post_action_delay", 1.2)))
        frame = self.adb_screenshot()
    auto_roi = tuple(cfg.get("auto_team_up_roi", (140, 1400, 980, 2050)))

    def locate_auto_team_up(current_frame):
        point = context._find_ocr_phrase_center(current_frame, "auto team up", auto_roi)
        if point is not None:
            return point
        auto_buttons = context._locate_green_rect_buttons(
            current_frame,
            auto_roi,
            min_width=300,
            max_width=500,
            min_height=80,
            max_height=160,
        )
        if auto_buttons:
            self.game_logger.info(
                "[%s] Found Auto Team-Up via green button at %s.",
                game_label,
                auto_buttons[0],
            )
            return auto_buttons[0]
        # The event changes this control from green to yellow in some states.
        point = context._locate_boomer_activate_button(current_frame, auto_roi)
        if point is not None:
            self.game_logger.info(
                "[%s] Found Auto Team-Up via yellow button at %s.",
                game_label,
                point,
            )
        return point

    auto_point = None
    auto_deadline = time.monotonic() + float(cfg.get("auto_team_up_timeout", 5.0))
    while True:
        auto_point = locate_auto_team_up(frame)
        if auto_point is not None or time.monotonic() >= auto_deadline:
            break
        time.sleep(float(cfg.get("auto_team_up_poll", 0.5)))
        frame = self.adb_screenshot()
    if auto_point is None:
        self.game_logger.warning("[%s] Danger Lurks opened without Auto Team-Up.", game_label)
        self._record_action(game_label, "boomer_auto_join", "failed", "Auto Team-Up control was not found")
        self._obs_capture("boomer_auto_team_up_missing", image=frame, game=game_label)
        self.ensure_base_view()
        return False

    # Text-based targeting intentionally accepts both green and yellow button
    # variants used by the event UI.
    self.adb_tap(*auto_point)
    time.sleep(float(cfg.get("post_action_delay", 1.2)))
    frame = self.adb_screenshot()
    activate_point = context._find_ocr_word_center(
        frame,
        "activate",
        tuple(cfg.get("activate_roi", (500, 1500, 1000, 2000))),
    )
    if activate_point is None:
        activate_point = context._locate_boomer_activate_button(
            frame,
            tuple(cfg.get("activate_roi", (500, 1500, 1000, 2000))),
        )
        if activate_point is not None:
            self.game_logger.info(
                "[%s] Found Activate via yellow button at %s.",
                game_label,
                activate_point,
            )
    if activate_point is None:
        self.game_logger.warning("[%s] Boomer Auto Team-Up dialog had no Activate button.", game_label)
        self._record_action(game_label, "boomer_auto_join", "failed", "Activate button was not found")
        self._obs_capture("boomer_activate_missing", image=frame, game=game_label)
        self.ensure_base_view()
        return False

    self.adb_tap(*activate_point)
    time.sleep(float(cfg.get("post_action_delay", 1.2)))
    result_frame = self.adb_screenshot()
    result_text = context._ocr_frame_text(result_frame, (200, 1150, 950, 1800), psm=11).lower()
    enabled = context._is_boomer_auto_join_enabled(result_text)
    if enabled:
        self.game_logger.info("[%s] Boomer Auto Team-Up enabled for 12 hours.", game_label)
        self._record_action(game_label, "boomer_auto_join", "success", "Danger Lurks Auto Team-Up enabled")
        self._schedule_check(f"boomer_auto_join_{game_label}", float(cfg.get("check_interval", 43200)))
        self._obs_event("boomer_auto_join", game=game_label, status="enabled")
    else:
        self.game_logger.warning("[%s] Boomer Auto Team-Up activation was not confirmed.", game_label)
        self._record_action(game_label, "boomer_auto_join", "failed", "Activation was not confirmed")
        self._obs_capture("boomer_auto_join_unconfirmed", image=result_frame, game=game_label)
    self.ensure_base_view()
    return enabled
