"""Healing services extracted from the application facade."""
import numpy as np
import time
import re
from bot.context import context


def _verify_healing_start(bot, frame, cfg):
    """A tap/world HUD is not proof: require an active or request-help icon."""
    for attempt in range(4):
        for name, key in (('heal_help_state','help_match_score'), ('heal_active','active_match_score')):
            match=context._find_masked_template_in_roi(frame,bot.templates.get(name),
                tuple(cfg['world_icon_roi']),float(cfg[key]))
            if match is not None:
                return name, frame, match
        if attempt < 3:
            time.sleep(.75)
            frame=bot.adb_screenshot()
    return None, frame, None


def do_heal_troops(self, game_name: str) -> bool:
    """Start one time-bounded Hospital batch and request alliance help."""
    cfg = context.CONFIG.get("healing", {})
    settings = context.CONFIG.get("game_settings", {}).get(game_name, {})
    if not cfg.get("enabled", False) or not settings.get("heal_troops", True):
        return False

    icon_roi = tuple(cfg["world_icon_roi"])

    def icon_match(frame, name: str, threshold_key: str):
        return context._find_masked_template_in_roi(
            frame, self.templates.get(name), icon_roi, float(cfg[threshold_key])
        )

    def tap_match_center(match, template_name: str):
        template = self.templates[template_name]
        self.adb_tap(
            int(match[0] + template.shape[1] // 2),
            int(match[1] + template.shape[0] // 2),
        )

    handled = False
    base_timeout = float(cfg.get("base_timeout", 20.0))
    if not self.ensure_base_view(timeout=base_timeout):
        self.game_logger.warning("Healing skipped for %s: base view was not available.", game_name)
        return False

    try:
        self.adb_tap(*context.CONFIG["action_coords"]["open_world"])
        time.sleep(context.CONFIG["timing"]["action_delay"])
        world_confirmed = self.confirm_screen(
            must_screen="world",
            timeout=float(cfg.get("world_transition_timeout", 10.0)),
            where="healing: open world",
        )
        frame = self.adb_screenshot()
        if not world_confirmed and frame is not None:
            # The world classifier is intentionally conservative because some
            # event overlays resemble its HUD.  A scoped Hospital icon is
            # stronger evidence for this workflow and lets healing continue
            # on valid map layouts that the generic classifier rejects.
            world_confirmed = any(
                icon_match(frame, template_name, threshold_key) is not None
                for template_name, threshold_key in (
                    ("heal_idle", "idle_match_score"),
                    ("heal_active", "active_match_score"),
                    ("heal_help_state", "help_match_score"),
                )
            )
            if world_confirmed:
                self.game_logger.info(
                    "Healing %s: using visible Hospital icon as world-view confirmation.",
                    game_name,
                )
        if not world_confirmed:
            self.game_logger.warning("Healing skipped for %s: world view did not open.", game_name)
            return False

        if frame is None:
            return False

        def healing_icon_state(candidate: np.ndarray | None) -> str | None:
            for template_name, threshold_key, state_name in (
                ("heal_help_state", "help_match_score", "help"),
                ("heal_active", "active_match_score", "active"),
                ("heal_idle", "idle_match_score", "idle"),
            ):
                if icon_match(candidate, template_name, threshold_key) is not None:
                    return state_name
            return None

        # World controls can still be sliding into place after the generic
        # world-screen confirmation.  Poll the tightly scoped toolbar before
        # concluding there is no Hospital work, while retaining the final
        # frame for completion-icon handling below.
        icon_state = healing_icon_state(frame)
        deadline = time.monotonic() + float(cfg.get("world_icon_wait_seconds", 8.0))
        poll_interval = max(0.2, float(cfg.get("world_icon_poll_interval", 0.75)))
        while icon_state is None and time.monotonic() < deadline:
            time.sleep(poll_interval)
            frame = self.adb_screenshot()
            icon_state = healing_icon_state(frame)
        if icon_state is None:
            self.game_logger.info(
                "Healing %s: no Hospital control appeared after %.1fs.",
                game_name,
                float(cfg.get("world_icon_wait_seconds", 8.0)),
            )
        else:
            self.game_logger.info("Healing %s: observed %s Hospital control.", game_name, icon_state)

        # Completion portraits differ by majority troop type.  Match every
        # captured variant and accept the first one visible in the icon slot.
        for template_name in cfg.get("completion_templates", ()):
            completion = context._find_masked_template_in_roi(
                frame,
                self.templates.get(template_name),
                icon_roi,
                float(cfg.get("completion_match_score", 0.10)),
            )
            if completion is None:
                continue
            template = self.templates[template_name]
            self.adb_tap(
                completion[0] + template.shape[1] // 2,
                completion[1] + template.shape[0] // 2,
            )
            self.game_logger.info("Accepted healing completion '%s' for %s.", template_name, game_name)
            time.sleep(context.CONFIG["timing"]["action_delay"])
            frame = self.adb_screenshot()
            handled = True
            break

        help_match = icon_match(frame, "heal_help_state", "help_match_score")
        if help_match is not None:
            tap_match_center(help_match, "heal_help_state")
            time.sleep(float(cfg.get("post_help_delay", 1.5)))
            after_help = self.adb_screenshot()
            help_remaining = icon_match(after_help, "heal_help_state", "help_match_score")
            active_now = icon_match(after_help, "heal_active", "active_match_score")
            if help_remaining is None and active_now is not None:
                self.game_logger.info("Alliance healing help requested for %s.", game_name)
                self._record_action(game_name, "troop_healing_help", "success", "Alliance help requested")
                return True
            self.game_logger.warning("Healing help tap was not visually confirmed for %s.", game_name)
            self._obs_capture(f"healing_help_unconfirmed_{game_name}", image=after_help, game=game_name)
            return handled

        active_match = icon_match(frame, "heal_active", "active_match_score")
        if active_match is not None:
            self.game_logger.debug("A healing batch is already active for %s.", game_name)
            return handled

        idle_match = icon_match(frame, "heal_idle", "idle_match_score")
        if idle_match is None:
            self.game_logger.debug("No healing action is visible for %s.", game_name)
            self._record_action(
                game_name, "troop_healing", "success" if handled else "nothing_to_do",
                "Healing completion accepted; no further batch available"
                if handled else "No Hospital healing action is available",
            )
            return handled

        tap_match_center(idle_match, "heal_idle")
        time.sleep(context.CONFIG["timing"]["action_delay"])
        hospital = self.adb_screenshot()
        title = context._ocr_frame_text(hospital, tuple(cfg["hospital_title_roi"]), psm=7)
        if "hospital" not in re.sub(r"[^a-z]", "", title.lower()):
            self.game_logger.warning("Healing skipped for %s: Hospital was not confirmed (%r).", game_name, title)
            self._obs_capture(f"healing_hospital_unconfirmed_{game_name}", image=hospital, game=game_name)
            return handled

        header_y = tuple(int(value) for value in cfg["hospital_row_header_y"])
        slider_y = tuple(int(value) for value in cfg["hospital_slider_y"])
        min_x = int(cfg["hospital_slider_min_x"])
        max_x = int(cfg["hospital_slider_max_x"])

        # Hospital remembers partial selections from the previous visit.  The
        # old reset dragged four handles from an assumed right edge, but a
        # partially selected handle is not at that coordinate and ignores the
        # drag.  Normalize through the Select All/Deselect toggle instead:
        # an all-selected state needs one tap, and a partial state needs two.
        # Re-read the Heal timer after each tap and stop only at confirmed zero.
        reset_duration = context._ocr_healing_duration_seconds(
            hospital, tuple(cfg["hospital_heal_time_roi"])
        )
        max_reset_taps = max(1, int(cfg.get("reset_max_toggle_taps", 2)))
        for reset_attempt in range(max_reset_taps):
            if reset_duration == 0:
                break
            self.game_logger.info(
                "Healing %s: resetting remembered selection via toggle %d/%d "
                "(duration=%s).",
                game_name,
                reset_attempt + 1,
                max_reset_taps,
                reset_duration,
            )
            self.adb_tap(*context.CONFIG["action_coords"]["hospital_select_all"])
            time.sleep(float(cfg.get("slider_settle_delay", 0.8)))
            hospital = self.adb_screenshot()
            reset_duration = context._ocr_healing_duration_seconds(
                hospital, tuple(cfg["hospital_heal_time_roi"])
            )

        if reset_duration != 0:
            self.game_logger.warning(
                "Healing skipped for %s: slider reset was not confirmed (duration=%s).",
                game_name,
                reset_duration,
            )
            self._obs_capture(
                f"healing_slider_reset_unconfirmed_{game_name}",
                image=hospital,
                game=game_name,
            )
            return handled

        availability = context._hospital_row_availability(hospital, header_y)
        if not availability or max(availability) <= 0:
            self.game_logger.warning("Healing skipped for %s: row counts unreadable (%s).", game_name, availability)
            self._obs_capture(f"healing_rows_unreadable_{game_name}", image=hospital, game=game_name)
            return handled

        row_index = max(range(len(availability)), key=availability.__getitem__)
        row_y = slider_y[row_index]
        current_x = int(cfg["hospital_slider_initial_x"])
        self.game_logger.info(
            "Healing %s: selecting row %d (OCR available=%d).",
            game_name, row_index + 1, availability[row_index],
        )
        self.adb_swipe(min_x, row_y, current_x, row_y, 450)
        time.sleep(float(cfg.get("slider_settle_delay", 0.8)))

        target = int(cfg["target_seconds"])
        tolerance = int(cfg["tolerance_seconds"])
        duration = None
        selection_frame = None
        lower_sample = None
        upper_sample = None
        max_adjustments = int(cfg.get("max_slider_adjustments", 4))
        for attempt in range(max_adjustments + 1):
            selection_frame = self.adb_screenshot()
            duration = context._ocr_healing_duration_seconds(
                selection_frame, tuple(cfg["hospital_heal_time_roi"])
            )
            if duration is None:
                self.game_logger.warning("Healing %s: Heal-button duration OCR failed.", game_name)
                self._obs_capture(f"healing_duration_unreadable_{game_name}", image=selection_frame, game=game_name)
                return handled
            self.game_logger.info(
                "Healing %s: slider x=%d gives %02d:%02d:%02d (target %02d:%02d:%02d).",
                game_name, current_x,
                duration // 3600, (duration % 3600) // 60, duration % 60,
                target // 3600, (target % 3600) // 60, target % 60,
            )
            if abs(duration - target) <= tolerance or attempt >= max_adjustments:
                break
            next_x, lower_sample, upper_sample = context._next_healing_slider_position(
                current_x,
                duration,
                target,
                min_x,
                max_x,
                lower_sample,
                upper_sample,
            )
            if next_x == current_x:
                break
            self.adb_swipe(current_x, row_y, next_x, row_y, 350)
            current_x = next_x
            time.sleep(float(cfg.get("slider_settle_delay", 0.8)))

        if duration is None or duration <= 0 or duration > int(cfg["hard_max_seconds"]):
            self.game_logger.warning(
                "Healing %s: refusing duration %s seconds (hard max=%s).",
                game_name, duration, cfg["hard_max_seconds"],
            )
            self._obs_capture(f"healing_duration_unsafe_{game_name}", image=selection_frame, game=game_name)
            return handled

        self.adb_tap(*context.CONFIG["action_coords"]["hospital_heal_confirm"])
        time.sleep(float(cfg.get("post_heal_delay", 2.0)))
        post_heal = self.adb_screenshot()
        if context._is_alliance_speedup_reward_dialog(post_heal):
            self.game_logger.info("Dismissing alliance speedup reward during healing.")
            self.adb_tap(*context.CONFIG["action_coords"]["healing_reward_confirm"])
            time.sleep(context.CONFIG["timing"]["action_delay"])
            post_heal = self.adb_screenshot()

        state, post_heal, confirmed_match = _verify_healing_start(self, post_heal, cfg)
        if state is None:
            self._record_action(game_name, 'troop_healing', 'failed',
                                'Heal tapped but active/help state was not verified; no blind retry')
            self._obs_capture(f"healing_post_confirm_unknown_{game_name}", image=post_heal, game=game_name)
            return handled

        self._record_action(game_name, "troop_healing", "success",
                            f"Batch visually verified ({state}); selected duration {duration} seconds")

        help_match = icon_match(post_heal, "heal_help_state", "help_match_score")
        if help_match is None:
            self.game_logger.info("Healing %s active; no request-help control visible.", game_name)
            return True

        tap_match_center(help_match, "heal_help_state")
        time.sleep(float(cfg.get("post_help_delay", 1.5)))
        after_help = self.adb_screenshot()
        help_remaining = icon_match(after_help, "heal_help_state", "help_match_score")
        active_now = icon_match(after_help, "heal_active", "active_match_score")
        if help_remaining is None and active_now is not None:
            self.game_logger.info("Healing batch and alliance help confirmed for %s.", game_name)
            self._record_action(
                game_name, "troop_healing_help", "success", "Alliance help requested"
            )
        else:
            self._record_action(game_name, 'troop_healing_help', 'failed',
                                'Alliance-help state transition was not confirmed')
            self.game_logger.warning("Healing %s started, but alliance help was not visually confirmed.", game_name)
            self._obs_capture(f"healing_started_help_unconfirmed_{game_name}", image=after_help, game=game_name)
        return True
    finally:
        self.ensure_base_view(timeout=base_timeout)
