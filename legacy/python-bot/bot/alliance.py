"""Alliance services extracted from the application facade."""
import time
from bot.context import context


def help_allies(self, game_name, frame=None):
    """Help teammates; count success only once the handshake clears."""
    cfg = context.CONFIG.get("alliance_help", {})
    if not cfg.get("enabled", True):
        return False
    if frame is None:
        frame = self.adb_screenshot()
    point = context._alliance_help_point(frame, self.templates)
    if point is None:
        return False
    for attempt in range(max(1, int(cfg.get("max_attempts", 2)))):
        self.game_logger.info("Helping alliance teammates at %s (attempt %d).", point, attempt + 1)
        self.adb_tap(*point)
        time.sleep(1.5)
        after = self.adb_screenshot()
        if after is None:
            break
        point = context._alliance_help_point(after, self.templates)
        if point is None:
            self.game_logger.info("Alliance teammate help confirmed: handshake shortcut cleared.")
            self._record_action(game_name, "passive_help", "success", "Ally-help handshake cleared after tap")
            self._obs_capture("alliance_teammate_help_confirmed", image=after, game=game_name)
            return True
    self.game_logger.warning("Alliance teammate help was not confirmed; handshake remained or screenshot failed.")
    self._record_action(game_name, "passive_help", "failed", "Ally-help shortcut did not clear")
    return False


def claim_all_mail_rewards(self, game_name: str | None = None) -> bool:
        """Visit every Mail tab and claim all available attached rewards."""
        game_label = game_name or "unknown"
        self.game_logger.info("[%s] Claiming rewards from all Mail tabs.", game_label)
        self._obs_event("mail_claim_start", game=game_label)
        mail_opened = False

        try:
            if not self.ensure_base_view():
                self.game_logger.warning("[%s] Base view not confirmed before Mail.", game_label)
                self._obs_event("mail_claim_end", game=game_label, status="base_not_confirmed")
                return False

            self.adb_tap(*context.CONFIG["action_coords"]["mail"])
            mail_opened = True
            if not self.confirm_screen(
                must_screen="mail",
                timeout=4.0,
                where="mail rewards: open",
            ):
                self.game_logger.warning("[%s] Mail screen did not open.", game_label)
                self._obs_capture(f"mail_open_failed_{game_label}", game=game_label)
                self._obs_event("mail_claim_end", game=game_label, status="open_failed")
                return False

            attempted_tabs = []
            for tab_name, tab_coords in context.CONFIG.get("mail_tabs", {}).items():
                current = self.adb_screenshot()
                if not self.is_screen("mail", current):
                    self.adb_tap(*context.CONFIG["action_coords"]["mail_reward_dismiss"])
                    time.sleep(context.CONFIG["timing"]["action_delay"])
                    current = self.adb_screenshot()
                if not self.is_screen("mail", current):
                    self.game_logger.warning(
                        "[%s] Mail screen was lost before tab %s; stopping.",
                        game_label,
                        tab_name,
                    )
                    self._obs_event(
                        "mail_claim_end",
                        game=game_label,
                        status="mail_screen_lost",
                        tab=tab_name,
                        attempted_tabs=attempted_tabs,
                    )
                    return False

                self.adb_tap(*tab_coords)
                time.sleep(context.CONFIG["timing"]["action_delay"])
                if not self.is_screen("mail", self.adb_screenshot()):
                    self.game_logger.warning(
                        "[%s] Mail tab %s did not become active; skipping.",
                        game_label,
                        tab_name,
                    )
                    continue

                self.adb_tap(*context.CONFIG["action_coords"]["mail_claim_all"])
                time.sleep(context.CONFIG["timing"]["action_delay"])
                attempted_tabs.append(tab_name)

                # Tabs with attached rewards show a full-screen Congratulations overlay.
                after_claim = self.adb_screenshot()
                if not self.is_screen("mail", after_claim):
                    self.game_logger.info(
                        "[%s] Dismissing Mail reward overlay for %s.",
                        game_label,
                        tab_name,
                    )
                    self.adb_tap(*context.CONFIG["action_coords"]["mail_reward_dismiss"])
                    time.sleep(context.CONFIG["timing"]["action_delay"])
                    if not self.confirm_screen(
                        must_screen="mail",
                        timeout=3.0,
                        where=f"mail rewards: after {tab_name}",
                    ):
                        self.game_logger.warning(
                            "[%s] Mail did not return after claiming %s.",
                            game_label,
                            tab_name,
                        )
                        return False

            configured_tabs = list(context.CONFIG.get("mail_tabs", {}))
            if attempted_tabs != configured_tabs:
                self.game_logger.warning(
                    "[%s] Mail scan incomplete: attempted %s of %s.",
                    game_label,
                    attempted_tabs,
                    configured_tabs,
                )
                self._obs_event(
                    "mail_claim_end",
                    game=game_label,
                    status="incomplete",
                    attempted_tabs=attempted_tabs,
                    configured_tabs=configured_tabs,
                )
                return False

            self.game_logger.info(
                "[%s] Mail Claim All completed for tabs: %s.",
                game_label,
                ", ".join(attempted_tabs),
            )
            self._obs_event(
                "mail_claim_end",
                game=game_label,
                status="ok",
                attempted_tabs=attempted_tabs,
            )
            return True
        except Exception as exc:
            self.game_logger.error(
                "[%s] Mail reward collection failed: %s",
                game_label,
                exc,
                exc_info=True,
            )
            self._obs_event("mail_claim_end", game=game_label, status="error", error=str(exc))
            return False
        finally:
            if mail_opened:
                self.adb_keyevent(111)
                time.sleep(context.CONFIG["timing"]["action_delay"])
                self.ensure_base_view()


def do_hourly_action(self, game_name: str | None = None):
        """Donate available Alliance Tech attempts and collect Alliance Gifts."""
        game_label = game_name or "unknown"
        # Both resources regenerate during the day. Daily completion remains in
        # historical status files, but must never suppress a later hourly run.
        tech_complete = False
        gifts_complete = False

        def screen_title_contains(expected: str, reads: int = 2) -> bool:
            observed = []
            for read_no in range(max(1, reads)):
                title = self.extract_text_from_roi(
                    x1=250,
                    y1=0,
                    x2=830,
                    y2=120,
                    device=self.device_id,
                    psm="7",
                )
                observed.append(title)
                if context._ocr_title_matches(title, expected):
                    return True
                if read_no + 1 < reads:
                    time.sleep(0.35)
            self.game_logger.warning(
                "[%s] Expected screen title %r, OCR read %r.",
                game_label,
                expected,
                observed,
            )
            return False

        def open_alliance_menu() -> bool:
            for attempt in range(1, 4):
                if not self.ensure_base_view(timeout=30.0, max_esc=10):
                    continue
                self.adb_tap(*context.CONFIG["action_coords"]["alliance"])
                time.sleep(context.CONFIG["timing"]["action_delay"])
                if screen_title_contains("Alliance"):
                    return True
                self.game_logger.warning(
                    "[%s] Alliance panel open attempt %d/3 was not confirmed; retrying.",
                    game_label,
                    attempt,
                )
                self.adb_keyevent(111)
                time.sleep(context.CONFIG["timing"]["action_delay"])
            return False

        def read_tech_attempts() -> tuple[int, int] | None:
            x1, y1, x2, y2 = context.CONFIG.get(
                "alliance_tech_attempts_roi",
                (570, 1430, 970, 1535),
            )
            text = self.extract_text_from_roi(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                device=self.device_id,
                psm="6",
                whitelist=None,
                save_debug=True,
            )
            counter = context._parse_attempts_fraction(text)
            self.game_logger.info(
                "[%s] Alliance Tech attempts OCR: %r -> %s.",
                game_label,
                text,
                counter,
            )
            return counter

        if not tech_complete:
            self.game_logger.info("[%s] Donating available Alliance Tech attempts.", game_label)
            if not open_alliance_menu():
                self._record_action(
                    game_label,
                    "alliance_tech_donations",
                    "failed",
                    "Alliance menu did not open",
                )
            else:
                self.adb_tap(*context.CONFIG["action_coords"]["alliance_techs"])
                time.sleep(context.CONFIG["timing"]["action_delay"])
                tech_frame = self.adb_screenshot()
                recommended_loc = None
                recommended_name = None
                for template_name in ("research_recommended2", "research_recommended"):
                    recommended_loc = self.find_template(
                        template_name,
                        tech_frame,
                        click=False,
                    )
                    if recommended_loc is not None:
                        recommended_name = template_name
                        break

                if recommended_loc is None or not screen_title_contains("Alliance Techs"):
                    self.game_logger.warning(
                        "[%s] Recommended Alliance Tech was not found.",
                        game_label,
                    )
                    self._obs_capture(
                        f"alliance_tech_recommended_missing_{game_label}",
                        game=game_label,
                        image=tech_frame,
                    )
                    self._record_action(
                        game_label,
                        "alliance_tech_donations",
                        "failed",
                        "Recommended Alliance Tech was not found",
                    )
                else:
                    template = self.templates[recommended_name]
                    recommended_x = recommended_loc[0] + template.shape[1] // 2
                    recommended_y = recommended_loc[1] + template.shape[0] // 2
                    self.adb_tap(recommended_x, recommended_y)
                    time.sleep(context.CONFIG["timing"]["action_delay"])

                    attempts = read_tech_attempts()
                    donation_round = 0
                    while attempts is not None and attempts[0] > 0 and donation_round < 5:
                        left, _ = attempts
                        self.game_logger.info(
                            "[%s] Donating to Alliance Tech %d time(s) this round.",
                            game_label,
                            left,
                        )
                        for _ in range(left):
                            self.adb_tap(*context.CONFIG["action_coords"]["alliance_tech_donate"])
                            time.sleep(max(0.8, context.CONFIG["timing"]["fast_click_delay"]))
                        time.sleep(context.CONFIG["timing"]["action_delay"])

                        attempts = None
                        for _ in range(4):
                            attempts = read_tech_attempts()
                            if attempts is not None:
                                break
                            time.sleep(0.75)
                        donation_round += 1

                    if attempts is not None and attempts[0] == 0:
                        self._record_action(
                            game_label,
                            "alliance_tech_donations",
                            "success",
                            "Alliance Tech donation attempts exhausted",
                            attempts_left=attempts[0],
                            total=attempts[1],
                        )
                        tech_complete = True
                    else:
                        self._record_action(
                            game_label,
                            "alliance_tech_donations",
                            "failed",
                            "Alliance Tech attempts did not reach zero",
                            counter=attempts,
                        )

        if not gifts_complete:
            self.game_logger.info("[%s] Collecting Common and Rare Alliance Gifts.", game_label)
            if not open_alliance_menu():
                self._record_action(
                    game_label,
                    "alliance_gifts",
                    "failed",
                    "Alliance menu did not open",
                )
            else:
                self.adb_tap(*context.CONFIG["action_coords"]["alliance_gifts"])
                time.sleep(context.CONFIG["timing"]["action_delay"])
                gifts_frame = self.adb_screenshot()
                if not screen_title_contains("Alliance Gifts"):
                    self._record_action(
                        game_label,
                        "alliance_gifts",
                        "failed",
                        "Alliance Gifts screen did not open",
                    )
                else:
                    common_claim_all = context._locate_green_rect_buttons(
                        gifts_frame,
                        (300, 1980, 780, 2140),
                        min_width=300,
                        max_width=450,
                        min_height=80,
                    )
                    if common_claim_all:
                        self.game_logger.info("[%s] Claiming all Common Alliance Gifts.", game_label)
                        self.adb_tap(*common_claim_all[0])
                        time.sleep(context.CONFIG["timing"]["action_delay"])
                        self.adb_tap(540, 1070)
                        time.sleep(context.CONFIG["timing"]["action_delay"])

                    common_remaining = context._locate_green_rect_buttons(
                        self.adb_screenshot(),
                        (300, 1980, 780, 2140),
                        min_width=300,
                        max_width=450,
                        min_height=80,
                    )
                    common_item_remaining = context._locate_green_rect_buttons(
                        self.adb_screenshot(),
                        (700, 850, 1020, 1900),
                        min_width=170,
                        max_width=260,
                        min_height=45,
                    )
                    self.adb_tap(*context.CONFIG["action_coords"]["alliance_gifts_rare"])
                    time.sleep(context.CONFIG["timing"]["action_delay"])
                    rare_claimed = 0
                    for _ in range(100):
                        rare_frame = self.adb_screenshot()
                        rare_buttons = context._locate_green_rect_buttons(
                            rare_frame,
                            (700, 850, 1020, 1900),
                            min_width=170,
                            max_width=260,
                            min_height=45,
                        )
                        if not rare_buttons:
                            break
                        self.adb_tap(*rare_buttons[0])
                        time.sleep(context.CONFIG["timing"]["action_delay"])
                        self.adb_tap(540, 1070)
                        time.sleep(context.CONFIG["timing"]["action_delay"])
                        rare_claimed += 1

                    remaining_rare = []
                    for _ in range(2):
                        remaining_rare = context._locate_green_rect_buttons(
                            self.adb_screenshot(),
                            (700, 850, 1020, 1900),
                            min_width=170,
                            max_width=260,
                            min_height=45,
                        )
                        if remaining_rare:
                            break
                        time.sleep(0.4)
                    gifts_screen_confirmed = screen_title_contains("Alliance Gifts")
                    if (
                        gifts_screen_confirmed
                        and not common_remaining
                        and not common_item_remaining
                        and not remaining_rare
                    ):
                        self._record_action(
                            game_label,
                            "alliance_gifts",
                            "success",
                            "Common Claim All and all Rare gifts processed",
                            rare_claimed=rare_claimed,
                        )
                        gifts_complete = True
                    else:
                        self._record_action(
                            game_label,
                            "alliance_gifts",
                            "failed",
                            "Alliance Gift claims remain",
                            common_remaining=len(common_remaining),
                            common_item_remaining=len(common_item_remaining),
                            rare_remaining=len(remaining_rare),
                            gifts_screen_confirmed=gifts_screen_confirmed,
                        )

        for _ in range(3):
            self.adb_keyevent(111)
            time.sleep(1)
        self.ensure_base_view(timeout=30.0, max_esc=10)
        return tech_complete and gifts_complete
