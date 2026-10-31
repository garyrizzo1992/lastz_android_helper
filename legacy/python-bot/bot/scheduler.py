"""Scheduler services extracted from the application facade."""
import time
import json
from status_store import ActionStatusStore, daily_period
from bot.context import context


def _rotation_timing_suggestion(
    durations: list[float] | tuple[float, ...],
    timing_cfg: dict | None = None,
) -> dict | None:
    """Summarize rolling cycle times and recommend a padded rotation window."""
    values = sorted(float(value) for value in durations if float(value) > 0)
    if not values:
        return None
    cfg = timing_cfg or {}
    sample_count = len(values)
    p90_index = max(0, ((9 * sample_count + 9) // 10) - 1)
    p90_seconds = values[p90_index]
    buffer_ratio = float(cfg.get("rotation_cycle_buffer_ratio", 1.20))
    buffered_seconds = max(120.0, p90_seconds * buffer_ratio)
    round_minutes = max(1, int(cfg.get("rotation_suggestion_round_minutes", 5)))
    rounded_minutes = int(
        (buffered_seconds + round_minutes * 60 - 1) // (round_minutes * 60)
    ) * round_minutes
    recommended_minutes = max(
        int(cfg.get("rotation_suggestion_min_minutes", 15)),
        min(int(cfg.get("rotation_suggestion_max_minutes", 45)), rounded_minutes),
    )
    return {
        "samples": sample_count,
        "average_seconds": sum(values) / sample_count,
        "p90_seconds": p90_seconds,
        "buffered_cycle_seconds": buffered_seconds,
        "recommended_minutes": recommended_minutes,
    }


def run_one_cycle(self, game_name):
        """Run one priority-ordered, independently scheduled account cycle.

        The cycle first establishes a known device/base state, then handles
        urgent maintenance (VIP, healing, visible passive actions), bounded
        daily/cooldown work, and finally opportunistic trucks and gathering.
        Expensive failures receive retry cooldowns and do not prevent later
        independent work.  Personal and world bounty paths are feature-gated.
        """
        cycle_start = time.time()
        self.game_logger.info(f"Starting cycle for {game_name}")
        self._trace_cycle_shots_left = int(context.CONFIG.get("internal_trace_max_shots_per_cycle", 8))
        self._obs_event("cycle_start", game=game_name, cycle_index=self.total_cycles + 1)

        if not self._adb_transport_ready():
            self._record_action(game_name, "device", "blocked", "USB device unavailable")
            time.sleep(min(30, max(1, self._transport_probe_after - time.monotonic())))
            return
        if not self.ensure_device_awake_unlocked(where=f"cycle_start:{game_name}"):
            if self._note_stuck(game_name, "device_locked_or_asleep"):
                self.recover_current_game(game_name, "device_locked_or_asleep")
            self._obs_event("cycle_end", game=game_name, status="skip_device_locked_or_asleep")
            self.status_store.mark_cycle(game_name, "failed", "Device was locked or asleep")
            return
        if not self.ensure_base_view():
            if self._note_stuck(game_name, "cycle_ensure_base_failed"):
                self.recover_current_game(game_name, "cycle_ensure_base_failed")
            self._obs_event("cycle_end", game=game_name, status="skip_base_not_confirmed")
            self.status_store.mark_cycle(game_name, "failed", "Base view was not confirmed")
            return
        screenshot = self.adb_screenshot()
        if screenshot is None:
            self.logger.warning("Failed to get screenshot. Skipping cycle.")
            self._obs_capture(f"cycle_skip_no_screenshot_{game_name}", game=game_name)
            if self._note_stuck(game_name, "screenshot_failed"):
                self.recover_current_game(game_name, "screenshot_failed")
            self._obs_event("cycle_end", game=game_name, status="skip_no_screenshot")
            self.status_store.mark_cycle(game_name, "failed", "Screenshot capture failed")
            return
        self._reset_stuck(game_name, "screenshot_failed")
        self._reset_stuck(game_name, "cycle_ensure_base_failed")

        actions_performed = []
        protected = (context.CONFIG.get("shield_activation", {}).get("protect_marches", True)
                     and self.shield_protection_active(game_name))
        if protected:
            self.game_logger.info("Shield safety mode: new manual marches are suppressed for %s.", game_name)

        vip_cfg = context.CONFIG.get('vip_rewards', {})
        if (vip_cfg.get('enabled', True) and not self._daily_action_complete(game_name, 'vip_rewards')
                and self._should_check(f'vip_rewards_{game_name}', vip_cfg.get('check_interval', 900))):
            if self.do_vip_rewards(game_name):
                actions_performed.append('vip_claimed')
            self._mark_check(f'vip_rewards_{game_name}')
            screenshot = self.adb_screenshot()

        # Urgent maintenance runs before long, failure-prone panel workflows.
        # Troop healing is checked from world view, then always returns to base.
        healing_cfg = context.CONFIG.get("healing", {})
        healing_check = f"troop_healing_{game_name}"
        if healing_cfg.get("enabled", False) and self._should_check(
            healing_check, float(healing_cfg.get("check_interval", 60))
        ):
            self.state_logger.info("Checking time-bounded troop healing...")
            if self.do_heal_troops(game_name):
                actions_performed.append("troop_healing")
            self._mark_check(healing_check)
            screenshot = self.adb_screenshot()

        # Passive Actions
        passive_check = f"passive_checks_{game_name}"
        if self._should_check(passive_check, context.CONFIG["timing"]["passive_checks_interval"]):
            self.state_logger.info("Checking passive actions...")

            def click_very_good_sign(frame):
                """Click the post-construction Very Good sign when OCR sees it."""
                point = context._find_ocr_phrase_center(frame, "very good")
                if point is None:
                    return frame, False
                self.game_logger.info(
                    "Clicking Very Good construction sign at (%d, %d).",
                    point[0], point[1],
                )
                self.adb_tap(*point)
                actions_performed.append("passive_very_good")
                self._record_action(
                    game_name,
                    "passive_very_good",
                    "success",
                    "Clicked the post-construction Very Good sign",
                )
                time.sleep(context.CONFIG["timing"]["action_delay"])
                return self.adb_screenshot(), True

            screenshot, _ = click_very_good_sign(screenshot)

            def collect_visible_build_completions(frame):
                """Accept every construction marker in the current base viewport."""
                clicks = 0
                previous_clicked_at = None
                for _ in range(50):
                    if frame is None:
                        break
                    clicked_at = self.find_template(
                        "build_complete", frame, click=True
                    )
                    if clicked_at is None:
                        break
                    if (
                        previous_clicked_at is not None
                        and abs(previous_clicked_at[0] - clicked_at[0]) <= 8
                        and abs(previous_clicked_at[1] - clicked_at[1]) <= 8
                    ):
                        self.game_logger.warning(
                            "Construction marker at (%d, %d) did not clear; moving to the next base view.",
                            clicked_at[0],
                            clicked_at[1],
                        )
                        break
                    previous_clicked_at = clicked_at
                    clicks += 1
                    actions_performed.append("passive_build_complete")
                    self._record_action(
                        game_name,
                        "passive_build_complete",
                        "success",
                        "Visible construction completion accepted",
                    )
                    # The green construction marker dismisses directly.  A
                    # short UI settle is sufficient and avoids doing slow OCR
                    # plus an unrelated fallback tap for every marker.
                    time.sleep(0.8)
                    frame = self.adb_screenshot()
                return frame, clicks

            # The visible viewport is cheap enough to inspect every passive
            # cycle.  The wider check is intentionally much less frequent and
            # must never chain swipes: accumulated camera drift can send the
            # base far off course.  Each move below is paired with its exact
            # reverse, restoring the centre before the next direction.
            screenshot, _ = collect_visible_build_completions(screenshot)
            base_scan_check = f"construction_completion_scan_{game_name}"
            base_scan_due = self._should_check(
                base_scan_check,
                context.CONFIG["timing"]["construction_completion_scan_interval"],
            )
            base_scan_pairs = [
                ("left",  (850, 1050, 250, 1050), (250, 1050, 850, 1050)),
                ("right", (250, 1050, 850, 1050), (850, 1050, 250, 1050)),
                ("up",    (540, 1450, 540, 750),  (540, 750, 540, 1450)),
                ("down",  (540, 750, 540, 1450),  (540, 1450, 540, 750)),
            ]
            if screenshot is not None and base_scan_due:
                for scan_index, (direction, outward_swipe, return_swipe) in enumerate(base_scan_pairs, 1):
                    self.game_logger.info(
                        "Scanning base for construction completions: %s check %d/%d.",
                        direction,
                        scan_index,
                        len(base_scan_pairs),
                    )
                    self.adb_swipe(*outward_swipe, duration_ms=600)
                    time.sleep(0.8)
                    screenshot = self.adb_screenshot()
                    screenshot, _ = collect_visible_build_completions(screenshot)
                    if screenshot is None:
                        break
                    # Always undo the exact swipe before considering another
                    # direction, even if that outer view had no completion.
                    self.adb_swipe(*return_swipe, duration_ms=600)
                    time.sleep(0.8)
                    screenshot = self.adb_screenshot()
                    if screenshot is None:
                        break
                self._mark_check(base_scan_check)
            elif screenshot is None and base_scan_due:
                self.game_logger.info(
                    "Skipping roaming construction scan because no screenshot is available."
                )
            else:
                self.game_logger.debug(
                    "Skipping full construction sweep; its independent cooldown is active."
                )

            passive_checks = ["exp", "food", "electric", "zent", "wood", "fuel", "fuel2", "fuel_can"]
            # A base can have several finished resource bubbles at once.  The
            # previous one-click limit left the rest until later cycles; clear
            # every visible resource-only bubble now.  Keep social/troop
            # controls single-click because their post-tap UI can vary.
            repeatable_passive_collects = {
                "exp", "food", "electric", "zent",
                "wood", "fuel", "fuel2", "fuel_can",
            }
            for name in passive_checks:
                max_clicks = 5 if name in repeatable_passive_collects else 1
                for _ in range(max_clicks):
                    if screenshot is None or not self.find_template(name, screenshot, click=True):
                        break
                    actions_performed.append(f"passive_{name}")
                    self._record_action(game_name, f"passive_{name}", "success", "Visible action collected")
                    time.sleep(context.CONFIG["timing"]["action_delay"])
                    screenshot = self.adb_screenshot()
                if screenshot is None:
                    break
            if self.help_allies(game_name, screenshot):
                actions_performed.append("passive_help")
            screenshot = self.adb_screenshot()
            self._mark_check(passive_check)
            self._record_action(game_name, "passive_actions", "success", "Passive action scan completed")

        # Mail rewards (once per Malta game day after the 04:00 reset)
        mail_check = f"mail_rewards_{game_name}"
        if self._daily_action_complete(game_name, "mail_rewards"):
            self.game_logger.debug(
                "Skipping Mail rewards for %s; today's scan is complete.",
                game_name,
            )
        elif self._should_check(
            mail_check,
            context.CONFIG["timing"]["mail_retry_interval"],
        ):
            self.state_logger.info("Checking daily Mail rewards...")
            if self.claim_all_mail_rewards(game_name):
                actions_performed.append("mail_rewards_claimed")
                self._mark_daily_action_complete(
                    game_name,
                    "mail_rewards",
                    "All Mail tabs checked",
                    tabs=list(context.CONFIG.get("mail_tabs", {})),
                )
            else:
                self._record_action(game_name, "mail_rewards", "failed", "Mail reward scan did not complete")
            self._mark_check(mail_check)
            screenshot = self.adb_screenshot()

        # Clear every completed troop-building marker before filling newly
        # empty queues.  A unit-cap hit is temporary, not a day-long
        # completion: retry it on a bounded interval so training resumes if
        # capacity later becomes available.
        training_cfg = context.CONFIG.get("troop_training", {})
        training_check = f"train_troops_{game_name}"
        unit_cap_check = f"troop_training_unit_cap_{game_name}"
        training_interval = float(context.CONFIG["timing"]["train_troops_check_interval"])
        unit_cap_interval = float(training_cfg.get("unit_cap_retry_interval", 3600))
        if (
            context.CONFIG["game_settings"].get(game_name, {}).get("train_troops", False)
            and self._should_check(training_check, training_interval)
        ):
            self.state_logger.info("Checking troop training...")
            collected = self.collect_completed_troops(game_name)
            if collected:
                actions_performed.append(f"troop_training_collected_{collected}")
            training_started = 0
            training_result = "unavailable"
            for _ in range(
                max(1, int(context.CONFIG.get("troop_training", {}).get("max_queues_per_cycle", 3)))
            ):
                # A full Military Center blocks new training, not collection.
                if not self._should_check(unit_cap_check, unit_cap_interval):
                    training_result = 'unit_cap'
                    break
                training_result = self.train_latest_troops(game_name)
                if training_result == "success":
                    training_started += 1
                    continue
                if training_result == "collected":
                    actions_performed.append("troop_training_collected")
                    # The panel itself still exposed a Claim/Collect action.
                    # Return to the base and continue; another training
                    # building may also have a completed queue.
                    continue
                if training_result == "unit_cap":
                    actions_performed.append("troop_training_paused_full")
                    self._mark_check(unit_cap_check)
                break
            if training_started:
                actions_performed.append(f"train_latest_troops_{training_started}")
            elif training_result == "unavailable":
                self._record_action(game_name, "troop_training", "unavailable", "No empty training queue")
            self._mark_check(training_check)
            screenshot = self.adb_screenshot()

        bounty_cfg = context.CONFIG.get('personal_bounties', {})
        bounty_check = f'personal_bounties_{game_name}'
        if bounty_cfg.get('enabled', False) and self._should_check(bounty_check, bounty_cfg.get('check_interval', 900)):
            if self.do_personal_bounties(game_name):
                actions_performed.append('personal_bounties')
            self._mark_check(bounty_check)
            screenshot = self.adb_screenshot()

        # Collect 8hrs chest
        chest_check = f"collect_8hrs_{game_name}"
        if self._should_check(chest_check, context.CONFIG["timing"]["collect_8hrs_check_interval"]):
            self.state_logger.info("Checking 8hrs chest collection...")
            # Refresh frame before matching (UI may have changed after prior actions)
            screenshot = self.adb_screenshot()
            if self.find_template("collect_8hrs", screenshot, click=True):
                self.game_logger.info("Collecting 8hrs chest")
                self.adb_tap(*context.CONFIG["action_coords"]["8hrs_chest_collect"])
                time.sleep(context.CONFIG["timing"]["action_delay"])
                self.ensure_base_view()
                actions_performed.append("collect_8hrs")
                self._record_action(game_name, "eight_hour_chest", "success", "Chest collected")
            else:
                self._record_action(game_name, "eight_hour_chest", "unavailable", "Chest not ready")
            self._mark_check(chest_check)

        # Construction and research are multi-screen workflows.  Their state
        # cannot change every few seconds, so do not reopen both panels on
        # every cycle.
        construction_check = f"construction_{game_name}"
        if self._should_check(
            construction_check,
            context.CONFIG["timing"]["construction_check_interval"],
        ):
            self.state_logger.info("Checking construction...")
            if self.do_build(game_name):
                actions_performed.append("construction")
            self._mark_check(construction_check)

        research_check = f"research_{game_name}"
        if self._should_check(
            research_check,
            context.CONFIG["timing"]["research_check_interval"],
        ):
            self.state_logger.info("Checking research...")
            if self.do_research(game_name):
                actions_performed.append("research")
                self._record_action(
                    game_name, "research", "success", "Research action completed"
                )
            else:
                self._record_action(
                    game_name,
                    "research",
                    "unavailable",
                    "No confirmed research action",
                )
            self._mark_check(research_check)

        # Tech donation attempts and gifts regenerate, so a daily completion
        # flag is incorrect. Revisit both on a bounded hourly cadence.
        alliance_check = f"alliance_{game_name}"
        if self._should_check(
            alliance_check,
            context.CONFIG["timing"]["alliance_check_interval"],
        ):
            if self.do_hourly_action(game_name):
                actions_performed.append("alliance_actions")
            self._mark_check(alliance_check)

        badge_cfg = context.CONFIG.get("alliance_shop_badges", {})
        badge_check = f"alliance_shop_badges_{game_name}"
        if badge_cfg.get("enabled", False) and self._should_check(
            badge_check, float(badge_cfg.get("check_interval", 604800))
        ):
            if self.do_alliance_shop_badges(game_name):
                actions_performed.append("alliance_shop_badges")
                self._mark_check(badge_check)

        shield_cfg = context.CONFIG.get("alliance_shop_shields", {})
        shield_check = f"alliance_shop_shields_{game_name}"
        if shield_cfg.get("enabled", False) and self._should_check(
            shield_check, float(shield_cfg.get("check_interval", 604800))
        ):
            if self.do_alliance_shop_shields(game_name):
                actions_performed.append("alliance_shop_shields")
                self._mark_check(shield_check)

        shop_catalog = context.CONFIG.get("alliance_shop_catalog", {})
        shop_catalog_check = f"alliance_shop_catalog_{game_name}"
        if shop_catalog.get("enabled", False) and self._should_check(
            shop_catalog_check, float(shop_catalog.get("check_interval", 604800))
        ):
            if self.do_alliance_shop_catalog(game_name):
                actions_performed.append("alliance_shop_catalog")
                self._mark_check(shop_catalog_check)
                reset_at = getattr(self, "_shop_reset_ts", {}).get(game_name)
                if reset_at is not None:
                    self._schedule_check(shop_catalog_check, reset_at - time.time())
            else:
                self._schedule_check(shop_catalog_check, float(shop_catalog.get("retry_interval", 900)))

        # Danger Lurks Auto Team-Up lasts 12 hours.  It is independent of
        # march dispatch, so renew it before the longer truck/radar workflows.
        boomer_cfg = context.CONFIG.get("boomer_auto_join", {})
        boomer_check = f"boomer_auto_join_{game_name}"
        boomer_interval = float(boomer_cfg.get("check_interval", 43200))
        if boomer_cfg.get("enabled", False) and self._should_check(
            boomer_check,
            boomer_interval,
        ):
            if self.do_boomer_auto_join(game_name):
                actions_performed.append("boomer_auto_join")
                self._mark_check(boomer_check)
            else:
                retry_interval = min(
                    boomer_interval,
                    max(1.0, float(boomer_cfg.get("retry_interval", 900))),
                )
                # _should_check compares now - last_check against the regular
                # interval. Backdate the failed attempt so it becomes due
                # after the bounded retry delay rather than another 12 hours.
                self.last_checks[boomer_check] = time.time() - boomer_interval + retry_interval
                self._schedule_check(boomer_check, retry_interval)
                self.game_logger.info(
                    "[%s] Boomer Auto Team-Up will retry in %.0f seconds.",
                    game_name,
                    retry_interval,
                )
            screenshot = self.adb_screenshot()

        # Trucks are a long panel workflow, so they run after maintenance and
        # daily work.  Mark failed attempts too; otherwise one bad screen
        # causes an immediate retry storm on every cycle.
        trucks_check = f"trucks_{game_name}"
        if self._should_check(
            trucks_check,
            context.CONFIG["timing"]["trucks_check_interval"],
        ):
            if self._daily_action_complete(game_name, "trucks"):
                self.game_logger.debug(
                    "Skipping trucks for %s; today's OCR-verified run is complete.",
                    game_name,
                )
            else:
                trades_left = self.do_trucks(game_name)
                if trades_left is not None:
                    self._reset_stuck(game_name, "trucks_failed")
                    self.game_logger.info(
                        "[%s] Trucks processing complete: %s trades remaining",
                        game_name,
                        trades_left,
                    )
                    if trades_left == 0:
                        actions_performed.append("trucks_exhausted")
                    else:
                        actions_performed.append(f"trucks_processed_{trades_left}")
                else:
                    actions_performed.append("trucks_failed")
                    if self._note_stuck(game_name, "trucks_failed"):
                        self.recover_current_game(game_name, "trucks_failed")
            self._mark_check(trucks_check)
            screenshot = self.adb_screenshot()

        # Disabled features are gated before entering their methods, avoiding
        # unnecessary scheduler churn, screenshots, and cooldown writes.
        if not protected and context.CONFIG.get("truck_plunder_enabled", False):
            truck_plunder_check = f"truck_plunder_{game_name}"
            if self._should_check(
                truck_plunder_check,
                context.CONFIG.get("truck_plunder_check_interval", 600),
            ):
                if self.do_truck_plunder(game_name):
                    actions_performed.append("truck_plunder")
                self._mark_check(truck_plunder_check)
                screenshot = self.adb_screenshot()

        # Radar combat/contest events get first use of a free march.  Normal
        # gathering runs immediately afterwards with whatever slots remain.
        radar_events_cfg = context.CONFIG.get("radar_events", {})
        radar_events_check = f"radar_events_{game_name}"
        if not protected and radar_events_cfg.get("enabled", False) and self._should_check(
            radar_events_check,
            float(radar_events_cfg.get("check_interval", 900)),
        ):
            radar_dispatches = self.process_radar_events(game_name)
            self._mark_check(radar_events_check)
            if radar_dispatches:
                actions_performed.append(f"radar_events_{radar_dispatches}")
            screenshot = self.adb_screenshot()

        # Periodic Actions (use fresh timestamps; earlier steps can take significant time)
        now_2min = time.time()
        if now_2min - self.last_2min_action_time >= context.CONFIG["timing"]["periodic_action_interval_2min"]:
            self.all_troops_busy = False
            self.last_2min_action_time = now_2min
            self.state_logger.info("Reset troop busy flag")

        if not protected and not self.all_troops_busy:
            self.state_logger.info("Attempting to send troops to gather")
            all_troops_busy = self.send_troops_gathering(game_name)
            # If gather aborted due to a failed screen check, clear the flag and
            # continue — gather already exited early, no need to kill the whole cycle.
            if getattr(self, "_abort_cycle", False):
                self._abort_cycle = False
                self.game_logger.info("Gather aborted by screen check; continuing cycle.")
                self._obs_event("gather_aborted", game=game_name, status="aborted_by_screen_check")
            if all_troops_busy:
                actions_performed.append("gather_troops_busy")
            elif getattr(self, "_last_gather_dispatches", 0) > 0:
                actions_performed.append("gather_troops_sent")
            else:
                actions_performed.append("gather_failed")

        # WORLD BOUNTY PLUNDER (bounded no-zoom scan)
        world_bounty_cfg = context.CONFIG.get("world_bounty", {})
        world_bounty_check = f"world_bounty_plunder_{game_name}"
        if not protected and world_bounty_cfg.get("enabled", False):
            if self._daily_action_complete(game_name, "world_bounty_plunder"):
                self.game_logger.info(
                    "Skipping world bounty plunder for %s; today's confirmed limit is complete.",
                    game_name,
                )
            elif self._should_check(
                world_bounty_check,
                float(world_bounty_cfg.get("check_interval", 900)),
            ):
                confirmed_plunders = self.plunder_world_bounties(game_name)
                self._mark_check(world_bounty_check)
                if confirmed_plunders:
                    actions_performed.append(f"world_bounties_{confirmed_plunders}")

        # Update cycle counter and log performance
        self.total_cycles += 1
        cycle_duration = time.time() - cycle_start
        self._perf_metrics['cycle_times'].append(cycle_duration)
        game_cycle_times = self._cycle_times_by_game.setdefault(game_name, [])
        game_cycle_times.append(cycle_duration)
        history_limit = max(
            1, int(context.CONFIG["timing"].get("rotation_history_samples", 20))
        )
        if len(game_cycle_times) > history_limit:
            del game_cycle_times[:-history_limit]
        
        # Keep only last 100 cycle times
        if len(self._perf_metrics['cycle_times']) > 100:
            self._perf_metrics['cycle_times'] = self._perf_metrics['cycle_times'][-100:]

        self.game_logger.info(f"Cycle completed in {cycle_duration:.2f}s. Actions: {actions_performed}")
        try:
            summary = self.status_store.account_summary(game_name)
            self.state_logger.info("[%s] Feature summary: %s", game_name, json.dumps(summary, sort_keys=True))
        except Exception as exc:
            self.state_logger.warning("Could not summarize %s: %s", game_name, exc)
        self._obs_event(
            "cycle_end",
            game=game_name,
            status="ok",
            duration_ms=int(cycle_duration * 1000),
            actions=actions_performed,
        )
        self.status_store.mark_cycle(
            game_name,
            "success",
            "Cycle completed",
            duration_seconds=round(cycle_duration, 2),
            actions=actions_performed,
        )
        
        # Log performance metrics every 10 cycles
        if self.total_cycles % 10 == 0:
            self._log_perf_metrics()
        
        time.sleep(context.CONFIG["timing"]["interval"])


def _next_daily_reset_ts(hour: int | None = None) -> float:
    """
    Return the Unix timestamp of the next occurrence of `hour`:00:00 local time.

    Used to calculate when daily truck trades reset.  If `hour` is None, reads
    CONFIG["daily_reset_hour"] (default 4, i.e. 04:00 AM).  If the current
    wall-clock time is already past today's reset hour, the timestamp returned
    is for tomorrow's reset.

    Parameters
    ----------
    hour : int, optional
        Local hour (0–23) at which the reset occurs.

    Returns
    -------
    float
        Unix epoch seconds for the next reset moment.
    """
    hour = int(hour if hour is not None else context.CONFIG.get("daily_reset_hour", 4))
    _, target = daily_period(
        timezone_name=context.CONFIG.get("status_timezone", "Europe/Malta"),
        reset_hour=hour,
    )
    return target.timestamp()


class SchedulerMixin:
    def _should_check(self, name: str, interval: float) -> bool:
        """Return True if at least `interval` seconds have passed since _mark_check(name)."""
        if not hasattr(self, "_check_intervals"):
            self._check_intervals = {}
        self._check_intervals[name] = interval
        try:
            stored = self.status_store.scheduled_at(name)
        except Exception as exc:
            self.state_logger.warning("Unable to read schedule %s: %s", name, exc)
            stored = None
        if stored is not None:
            return time.time() >= stored
        return (time.time() - self.last_checks.get(name, 0)) >= interval

    def _mark_check(self, name: str) -> None:
        """Record the current time as the last-checked timestamp for `name`."""
        self.last_checks[name] = time.time()
        interval = getattr(self, "_check_intervals", {}).get(name)
        if interval is not None:
            account = name.rsplit("_", 1)[-1]
            action = name[:-(len(account) + 1)]
            action = {"train_troops": "troop_training", "collect_8hrs": "eight_hour_chest"}.get(action, action)
            try:
                result = self.status_store.account_summary(account).get(action, {})
                if result.get("result") == "failed":
                    interval = min(interval, float(context.CONFIG.get("workflow_failure_retry_interval", 900)))
            except Exception as exc:
                self.state_logger.warning("Unable to read workflow result for %s: %s", name, exc)
            self._schedule_check(name, interval)

    def _schedule_check(self, name: str, delay: float) -> None:
        interval = getattr(self, "_check_intervals", {}).get(name, delay)
        self.last_checks[name] = time.time() - interval + max(1.0, delay)
        try:
            self.status_store.schedule(name, time.time() + max(1.0, delay))
        except Exception as exc:
            self.state_logger.warning("Unable to persist schedule %s: %s", name, exc)

    def _daily_action_complete(self, game_name: str, action: str) -> bool:
        try:
            return self.status_store.daily_complete(game_name, action)
        except Exception as exc:
            self.state_logger.warning("Unable to read daily %s status for %s: %s", action, game_name, exc)
            return False

    def _mark_daily_action_complete(self, game_name: str, action: str, message: str = "", **details) -> None:
        try:
            self.status_store.mark_daily_complete(game_name, action, message, **details)
        except Exception as exc:
            self.state_logger.warning("Unable to persist daily %s status for %s: %s", action, game_name, exc)
