"""Training services extracted from the application facade."""
import cv2
import numpy as np
import time
import re
from bot.context import context


def _completion_marker(bot, frame, near=None):
    """Strict portrait matching, then a colour/shape-specific completion tick."""
    if frame is None:
        return None
    if near is not None:
        x,y=near
        scoped=np.zeros_like(frame)
        scoped[max(0,y-130):y+130,max(0,x-130):x+130]=frame[max(0,y-130):y+130,max(0,x-130):x+130]
        frame=scoped
    cfg = context.CONFIG.get('troop_training', {})
    names = cfg.get('completion_templates', ('raider', 'assulter', 'shooter'))
    for name in names:
        match = bot.find_template(name, frame, threshold=0.05, click=False)
        if match is not None:
            template = bot.templates[name]
            return name, int(match[0]+template.shape[1]//2), int(match[1]+template.shape[0]//2)
    green = cv2.inRange(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV), (35,140,160), (85,255,255))
    roi = (150, 350, frame.shape[1]-50, frame.shape[0]-200)
    for name in ('troop_completion_tick', 'troop_completion_tick_timer'):
        template = bot.templates.get(name)
        if template is None:
            continue
        tick = template[:, :, 3]
        for scale in (1.0, .94, 1.06):
            scaled = cv2.resize(tick, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
            hits = context._template_match_centers(cv2.cvtColor(green,cv2.COLOR_GRAY2BGR),
                scaled, roi, threshold=.88, max_matches=3)
            for x,y,_ in hits:
                # Completed troop ticks overlap a gold portrait. A green
                # arrow/check elsewhere on the base is not a troop claim.
                portrait=frame[max(0,y-110):y+5,max(0,x-110):x+10]
                gold=cv2.inRange(cv2.cvtColor(portrait,cv2.COLOR_BGR2HSV),
                                 (15,80,120),(35,255,255))
                if cv2.countNonZero(gold)/gold.size >= .04:
                    return name,x,y
    return None


def collect_completed_troops(self, game_name: str) -> int:
    """Collect every visible completed troop queue from the base.

    Training completion markers are distinct from resource bubbles: they
    represent three different troop buildings and can all be present at once.
    Keep this workflow separate from passive actions so it is bounded,
    observable, and always runs before opening a new training queue.
    """
    cfg = context.CONFIG.get("troop_training", {})
    if not self.ensure_base_view():
        self.game_logger.warning(
            "[%s] Completed troop collection skipped because base view was not confirmed.",
            game_name,
        )
        return 0

    template_names = tuple(cfg.get("completion_templates", ("raider", "assulter", "shooter")))
    max_collections = max(1, int(cfg.get("max_collections_per_cycle", len(template_names))))
    collected = 0

    for _ in range(max_collections):
        frame = self.adb_screenshot()
        if frame is None:
            break

        clicked = _completion_marker(self, frame)
        if clicked is None:
            break

        self.adb_tap(clicked[1], clicked[2])
        time.sleep(float(cfg.get("post_collection_delay", 1.0)))
        if not self.ensure_base_view():
            self.game_logger.warning(
                "[%s] Troop completion click did not return to base view.", game_name
            )
            break

        after = self.adb_screenshot()
        if after is None:
            self._record_action(game_name, 'troop_training_collection', 'failed',
                                'No screenshot available to verify collection')
            break
        remaining = _completion_marker(self, after, near=clicked[1:])
        if remaining and abs(remaining[1]-clicked[1]) <= 60 and abs(remaining[2]-clicked[2]) <= 60:
            self._record_action(game_name, 'troop_training_collection', 'failed',
                                'Completion marker remained after collection tap')
            break
        collected += 1
        self.game_logger.info(
            "[%s] Accepted completed troops from %s queue (%d/%d).",
            game_name,
            clicked[0],
            collected,
            max_collections,
        )
        self._record_action(
            game_name,
            "troop_training_collection",
            "success",
            f"Completed troops accepted from {clicked[0]} queue",
        )

    return collected


def train_latest_troops(self, game_name: str) -> str:
    """Fill one empty troop queue with the highest unlocked visible tier.

    Completed queues are collected separately by ``collect_completed_troops``
    before this method is entered.
    """
    cfg = context.CONFIG.get("troop_training", {})
    if not self.ensure_base_view():
        self.game_logger.warning("[%s] Troop training skipped because base view was not confirmed.", game_name)
        return "failed"
    if not self.wait_for_template("empty_troops", timeout=3.0, threshold=0.05, click=True):
        self._record_action(game_name, "troop_training", "unavailable", "No idle training queue visible")
        return "unavailable"
    time.sleep(float(cfg.get("panel_open_delay", 1.5)))

    panel = self.adb_screenshot()
    if self._troop_unit_cap_reached(panel):
        self.game_logger.info(
            "[%s] Military Center is already full; training deferred.",
            game_name,
        )
        self._record_action(
            game_name,
            "troop_training",
            "unavailable",
            "Military Center unit cap reached; training deferred",
        )
        self.ensure_base_view()
        return "unit_cap"

    # A finished queue can require an explicit Claim/Collect before its slot
    # becomes trainable again.  Resolve that first instead of reporting the
    # queue as unavailable and leaving trained troops unaccepted.
    completion_roi = tuple(cfg.get("completion_action_roi", (450, 600, 1050, 1900)))
    completion_point = context._find_ocr_word_center(panel, "claim", completion_roi)
    completion_label = "Claim"
    if completion_point is None:
        completion_point = context._find_ocr_word_center(panel, "collect", completion_roi)
        completion_label = "Collect"
    if completion_point is not None:
        self.game_logger.info(
            "[%s] Accepting completed trained troops via %s at (%d, %d).",
            game_name,
            completion_label,
            completion_point[0],
            completion_point[1],
        )
        self.adb_tap(*completion_point)
        time.sleep(float(cfg.get("post_train_delay", 2.0)))
        after = self.adb_screenshot()
        if (after is None or context._find_ocr_word_center(after, 'claim', completion_roi)
                or context._find_ocr_word_center(after, 'collect', completion_roi)):
            self._record_action(game_name, 'troop_training_collection', 'failed',
                                'Claim/Collect did not visibly clear')
            self.ensure_base_view()
            return 'failed'
        self._record_action(
            game_name,
            "troop_training_collection",
            "success",
            "Completed trained troops accepted",
        )
        self.ensure_base_view()
        return "collected"

    centers = tuple(int(value) for value in cfg.get("tier_centers", (150, 370, 585, 805, 1015)))
    card_y = tuple(int(value) for value in cfg.get("tier_card_y", (1690, 1875)))

    def card_states(frame: np.ndarray | None) -> list[dict]:
        return context._troop_tier_card_states(
            frame,
            context._visible_troop_card_centers(frame, card_y, centers),
            card_y=card_y,
            half_width=int(cfg.get("tier_card_half_width", 75)),
            unlocked_ratio=float(cfg.get("unlocked_color_ratio", 0.15)),
            selected_ratio=float(cfg.get("selected_yellow_ratio", 0.005)),
        )

    highest = None
    states = card_states(panel)
    max_swipes = max(0, int(cfg.get("max_selector_swipes", 5)))
    for swipe_index in range(max_swipes + 1):
        highest = context._highest_visible_unlocked_troop_card(states)
        if highest is None:
            self.game_logger.warning("[%s] No unlocked troop tier card was detected.", game_name)
            self._obs_capture(
                f"troop_training_no_unlocked_tier_{game_name}",
                image=panel,
                game=game_name,
            )
            self.ensure_base_view()
            return "failed"

        locked_to_right = any(
            state["index"] > highest["index"] and not state["unlocked"]
            for state in states
        )
        if locked_to_right:
            break
        if swipe_index >= max_swipes:
            if max_swipes == 0:
                # The selector may already be positioned at its right edge,
                # leaving no locked card in the calibrated row.  In that
                # case the rightmost *visible* unlocked card is the safest
                # available choice; aborting here prevented all training.
                self.game_logger.info(
                    "[%s] No locked tier is visible; selecting the rightmost visible unlocked tier.",
                    game_name,
                )
                break
            self.game_logger.warning(
                "[%s] Could not reach the first locked troop tier after %d swipes.",
                game_name,
                max_swipes,
            )
            self._obs_capture(
                f"troop_training_tier_end_unknown_{game_name}",
                image=panel,
                game=game_name,
            )
            self.ensure_base_view()
            return "failed"

        start_x, start_y, end_x, end_y = (
            int(value)
            for value in cfg.get("selector_swipe", (900, 1780, 300, 1780))
        )
        self.adb_swipe(
            start_x,
            start_y,
            end_x,
            end_y,
            int(cfg.get("selector_swipe_duration", 350)),
        )
        time.sleep(float(cfg.get("selector_settle_delay", 0.8)))
        previous_panel = panel
        panel = self.adb_screenshot()
        self._obs_capture("troop_selector_swipe", image=panel, game=game_name, swipe=swipe_index + 1)
        states = card_states(panel)
        if previous_panel is not None and panel is not None:
            row_before = previous_panel[card_y[0]:card_y[1]]
            row_after = panel[card_y[0]:card_y[1]]
            if row_before.shape == row_after.shape and float(np.mean(cv2.absdiff(row_before, row_after))) < 1.5:
                # The actual right edge was reached, including accounts that
                # have unlocked every tier in this building.
                highest = context._highest_visible_unlocked_troop_card(states)
                break

    self.game_logger.info(
        "[%s] Selecting highest unlocked troop tier at %s (color score %.3f).",
        game_name,
        highest["center"],
        highest["unlocked_score"],
    )
    self.adb_tap(*highest["center"])
    time.sleep(float(cfg.get("selection_settle_delay", 0.8)))
    selected_frame = self.adb_screenshot()
    selected_states = card_states(selected_frame)
    # Confirm the card we actually tapped, not whichever card happens to be
    # rightmost after the selector animation.  The latter can be a different
    # card when the carousel has settled a few pixels away from its old
    # position.
    selected_target = next(
        (state for state in selected_states if abs(state["center"][0] - highest["center"][0]) < 55),
        None,
    )
    train_roi = tuple(cfg.get("train_button_roi", (550, 1900, 1080, 2150)))
    train_buttons = context._locate_green_rect_buttons(
        selected_frame,
        train_roi,
        min_width=int(cfg.get("train_button_min_width", 300)),
        max_width=int(cfg.get("train_button_max_width", 500)),
        min_height=int(cfg.get("train_button_min_height", 70)),
        max_height=int(cfg.get("train_button_max_height", 180)),
    )
    # In the training UI, the usable Train action is blue while Speed Up is
    # green.  Accept both visual variants, then prefer OCR where available.
    train_buttons.extend(
        context._locate_green_rect_buttons(
            selected_frame,
            train_roi,
            min_width=int(cfg.get("train_button_min_width", 300)),
            max_width=int(cfg.get("train_button_max_width", 500)),
            min_height=int(cfg.get("train_button_min_height", 70)),
            max_height=int(cfg.get("train_button_max_height", 180)),
            hsv_lower=(90, 70, 70),
            hsv_upper=(130, 255, 255),
        )
    )
    train_buttons = sorted(set(train_buttons), key=lambda point: (point[1], point[0]))
    train_point = context._find_ocr_word_center(
        selected_frame,
        "train",
        train_roi,
    )
    if selected_target is None or not selected_target["selected"]:
        self.game_logger.warning("[%s] Highest troop tier selection was not visually confirmed.", game_name)
        self._obs_capture(
            f"troop_training_tier_unconfirmed_{game_name}",
            image=selected_frame,
            game=game_name,
        )
        self.ensure_base_view()
        return "failed"
    if not (train_buttons or train_point):
        self.game_logger.warning("[%s] Train button was not found after tier selection.", game_name)
        self._obs_capture(
            f"troop_training_button_missing_{game_name}",
            image=selected_frame,
            game=game_name,
        )
        self.ensure_base_view()
        return "failed"

    # Prefer the OCR-confirmed Train label.  The same green geometry is used
    # for Go and Speed Up, so it is only a fallback when OCR is unavailable.
    train_tap = train_buttons[-1] if train_buttons else train_point
    self.game_logger.info("[%s] Tapping Train at %s (OCR label %s).", game_name, train_tap, train_point)
    self._obs_capture("troop_training_selected", image=selected_frame, game=game_name, train_tap=train_tap)
    self.adb_tap(*train_tap)
    time.sleep(.25)
    early_response = self.adb_screenshot()
    self._obs_capture("troop_training_early_response", image=early_response, game=game_name)
    time.sleep(max(0, float(cfg.get("post_train_delay", 2.0)) - .25))
    result_frame = self.adb_screenshot()
    warning_text = context._ocr_frame_text(result_frame, (150, 700, 950, 1450), psm=6)
    if context._is_lower_tier_training_warning(warning_text):
        # A usable Train button does not prove the latest tier was selected.
        # Never confirm this warning and silently train an obsolete unit.
        cancel = context._find_ocr_word_center(result_frame, "cancel", (100, 1000, 950, 1600))
        if cancel:
            self.adb_tap(*cancel)
        else:
            self.adb_keyevent(111)
        self._record_action(game_name, "troop_training", "failed", "Higher tier available; lower-tier training cancelled")
        self._obs_capture("troop_training_lower_tier_rejected", image=result_frame, game=game_name)
        self.ensure_base_view()
        return "failed"
    if self._troop_unit_cap_reached(result_frame) or self._troop_unit_cap_reached(early_response):
        self.game_logger.info(
            "[%s] Military Center unit cap reached; will retry after the configured cooldown.",
            game_name,
        )
        self._obs_capture(
            f"troop_training_unit_cap_{game_name}",
            image=result_frame,
            game=game_name,
        )
        self._record_action(
            game_name,
            "troop_training",
            "unavailable",
            "Military Center unit cap reached; training deferred",
        )
        self.adb_tap(*context.CONFIG["action_coords"]["train_troops_cap_close"])
        time.sleep(context.CONFIG["timing"]["action_delay"])
        self.ensure_base_view()
        return "unit_cap"

    # Starting a queue does *not* close this panel on current game versions:
    # it changes Train into Speed Up and shows "Training in progress".  The
    # former green-button-only check consequently treated a real Speed Up
    # control as an unchanged Train button and recorded a false failure.
    progress_roi = tuple(cfg.get("training_progress_roi", (80, 1220, 1030, 1620)))
    progress_text = context._ocr_frame_text(result_frame, progress_roi, psm=11)
    progress_normalized = re.sub(r"[^a-z]+", "", progress_text.lower())
    training_confirmed = "traininginprogress" in progress_normalized
    confirmation = "active queue" if training_confirmed else ""
    if not training_confirmed and self.is_screen("home", result_frame):
        training_confirmed = True
        confirmation = "base view"
    if not training_confirmed:
        deadline = time.monotonic() + float(cfg.get("post_train_confirm_timeout", 4.0))
        while time.monotonic() < deadline:
            time.sleep(0.5)
            result_frame = self.adb_screenshot()
            progress_text = context._ocr_frame_text(result_frame, progress_roi, psm=11)
            progress_normalized = re.sub(r"[^a-z]+", "", progress_text.lower())
            if "traininginprogress" in progress_normalized:
                training_confirmed = True
                confirmation = "active queue"
                break
            if self.is_screen("home", result_frame):
                training_confirmed = True
                confirmation = "base view"
                break
    if not training_confirmed:
        # OCR distinguishes a real Train label from the visually identical
        # green Speed Up button shown for an already-running queue.
        train_still_visible = context._find_ocr_word_center(
            result_frame,
            "train",
            tuple(cfg.get("train_button_roi", (550, 1900, 1080, 2150))),
        ) is not None
        self.game_logger.warning(
            "[%s] Training was not confirmed (%s).",
            game_name,
            "Train label remained visible"
            if train_still_visible
            else "base view did not return",
        )
        self._obs_capture(
            f"troop_training_start_unconfirmed_{game_name}",
            image=result_frame,
            game=game_name,
            train_button_visible=train_still_visible,
            training_progress_text=progress_text[:200],
        )
        self._record_action(game_name, "troop_training", "failed", "Training start was not confirmed")
        self.ensure_base_view()
        return "failed"

    self.game_logger.info(
        "[%s] Highest unlocked troop tier training started (%s confirmed).",
        game_name,
        confirmation,
    )
    self._record_action(
        game_name,
        "troop_training",
        "success",
        "Highest unlocked troop tier selected and training started",
    )
    self.ensure_base_view()
    return "success"
