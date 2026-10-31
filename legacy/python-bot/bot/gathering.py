"""Gathering services extracted from the application facade."""
import time
import random
from bot.context import context


def select_resource_level(self, level=None):
        """
        Tap the resource-level filter button in the gather search panel.

        The gather UI shows a row of numbered buttons (1–6) that filter the
        world map to display only resource nodes of that tier.  Coordinates
        for each level are in CONFIG["resource_levels"].

        Parameters
        ----------
        level : int, optional
            Resource level to select (1–6).  If None, a random level
            between 3 and 6 is chosen, targeting higher-yield nodes.

        Returns
        -------
        bool
            True if the level is valid and was tapped, False otherwise.
        """
        if level is None:
            level = random.randint(4, 6)
        
        self.game_logger.debug(f"Selecting resource level: {level}")
        coords = context.CONFIG["resource_levels"].get(level)
        if coords:
            self.adb_tap(coords[0], coords[1])
            time.sleep(context.CONFIG["timing"]["action_delay"])
            return True
        else:
            self.game_logger.warning(f"Invalid resource level: {level}")
            return False


def search_and_gather_resource(self, resource_type):
        """
        Locate a resource node of the given type on the world map and select it.

        The gather search panel shows the world map filtered to a specific
        resource type.  This function looks for the resource's yield panel
        template (lumberyard / farmyard / zentyard) in the current view, then
        systematically swipes right and left up to max_swipes times each to
        scan the map until the template is found.

        Resource type to template mapping
        ----------------------------------
        "Wood" → "lumberyard"  (images/lumberyard.png)
        "Food" → "farmyard"    (images/farmyard.png)
        "Zent" → "zentyard"    (images/zentyard.png)  — weight=0 so never chosen

        When the template is found and clicked, select_resource_level() is
        called to also tap the level filter button.

        Parameters
        ----------
        resource_type : str
            One of "Wood", "Food", or "Zent".

        Returns
        -------
        bool
            True if the resource panel was found and clicked, False if the
            systematic swipe search was exhausted without finding it.
            Either way, select_resource_level() is called as a fallback.
        """
        self.game_logger.info(f"Searching for {resource_type}")
        
        # Map resource types to their template names
        resource_templates = {
            "Wood": "lumberyard",
            "Food": "farmyard", 
            "Zent": "zentyard"
        }
        
        target_template = resource_templates.get(resource_type)
        if not target_template:
            self.game_logger.warning(f"Unknown resource type: {resource_type}")
            return False
        
        # First, check if the resource is visible in current view
        screenshot = self.adb_screenshot()
        if self.find_template(target_template, screenshot, click=True):
            time.sleep(context.CONFIG["timing"]["action_delay"])
            self.game_logger.info(f"Found {resource_type} in current view")
            self.select_resource_level()
            return True
        
        # Define swipe parameters
        screen_width = screenshot.shape[1] if screenshot is not None else 1080

        start_x = int(screen_width * 0.7)   # Start from 70% of screen width
        end_x = int(screen_width * 0.6)     # End at 60% of screen width
        center_y = int(1447)  # Middle of screen vertically
        
        max_swipes = 5  # Maximum swipes in each direction
        
        # Search by swiping right first (swipe left to move view right)
        self.game_logger.debug(f"Searching for {resource_type} by swiping right...")
        for attempt in range(max_swipes):
            self.adb_swipe(start_x, center_y, end_x, center_y, context.CONFIG["timing"]["swipe_duration"])
            time.sleep(context.CONFIG["timing"]["action_delay"])
            
            screenshot = self.adb_screenshot()
            if screenshot is not None and self.find_template(target_template, screenshot, click=True):
                self.game_logger.info(f"Found {resource_type} after swiping right {attempt + 1} times")
                self.select_resource_level()
                return True
        
        # Search by swiping left (swipe right to move view left)
        self.game_logger.debug(f"Searching for {resource_type} by swiping left...")
        for attempt in range(max_swipes * 2):  # Swipe back and then some more
            self.adb_swipe(end_x, center_y, start_x, center_y, context.CONFIG["timing"]["swipe_duration"])
            time.sleep(context.CONFIG["timing"]["action_delay"])
            
            screenshot = self.adb_screenshot()
            if screenshot is not None and self.find_template(target_template, screenshot, click=True):
                self.game_logger.info(f"Found {resource_type} after swiping left {attempt + 1} times")
                self.select_resource_level()
                return True
        
        # Resource not found after all attempts
        self.game_logger.warning(f"Could not find {resource_type} after systematic search")
        self.select_resource_level()  # Attempt to select anyway as fallback
        return False


def send_troops_gathering(self, game_name):
        """
        Send available march slots to gather resources on the world map.

        This function runs a loop of up to 10 send attempts.  Each attempt:

        1.  Tap the "open_world" button to enter the world map view.
        2.  confirm_screen(none_of=["home"]) to verify the world map opened;
            abort the whole gather loop if not (sets _abort_cycle flag).
        3.  Parse the right-side march sidebar: count badge plus per-slot
            marching / idle / gathering status. If used >= total, all slots
            are busy; close the world map, set self.all_troops_busy = True,
            and return True.
        4.  Tap "search_button" to open the gather search panel.
        5.  Pick a random resource type (Food 50 %, Wood 50 %, Zent 0 %) via
            random.choices() weighted selection.
        6.  Call search_and_gather_resource() to locate and tap the resource
            node panel.
        7.  Tap gather_search -> middle_screen -> gather_button ->
            gather_confirm_march to send the march.
            Re-parse the sidebar afterwards to confirm the dispatch changed
            the active/idle slot state.
        8.  Call do_radar(game_name) to dismiss radar alerts and report treasure.
        9.  ensure_base_view() then do_trucks() between attempts.

        If _abort_cycle is set by any inner confirm_screen call, the loop
        exits immediately and returns False so run_one_cycle() can restart.

        Parameters
        ----------
        game_name : str
            Used only for logging and observability events.

        Returns
        -------
        bool
            True  if all march slots are confirmed busy via sidebar parsing.
            False if max_attempts were reached or the cycle was aborted.
        """
        self.game_logger.info("Performing gather resource action.")
        self._obs_event("gather_start", game=game_name)
        self._last_gather_dispatches = 0
        if not self.ensure_base_view():
            if self._note_stuck(game_name, "ensure_base_before_gather"):
                self.recover_current_game(game_name, "ensure_base_before_gather")
            self._record_action(game_name, "gathering", "failed", "Base view was not confirmed")
            return False

        max_attempts = max(1, int(context.CONFIG.get("gather_max_attempts", 10)))
        for attempt in range(1, max_attempts + 1):
            self.game_logger.info(f"Gather attempt {attempt}/{max_attempts}")
            self._obs_event("gather_attempt", game=game_name, attempt=attempt, max_attempts=max_attempts)
            # Open world and small delay
            opened_world = self.tap_then_confirm(
                "gather: open_world",
                lambda: self.adb_tap(*context.CONFIG["action_coords"]["open_world"]),
                any_of=["hq", "hq2"],
                none_of=["home"],
                must_screen="world",
                timeout=3.0,
                retries=2,
                abort_on_fail=True,
            )
            # Abort if world didn’t open
            if not opened_world:
                self._obs_event("gather_abort", game=game_name, reason="world_not_opened", attempt=attempt)
                if self._note_stuck(game_name, "world_not_opened"):
                    self.recover_current_game(game_name, "world_not_opened")
                return False

            # Parse right-side march sidebar; if used >= total, we're done.
            before_status = self.read_march_status(where=f"gather attempt {attempt} before dispatch")
            before_count = self.march_count(before_status)
            if before_count:
                used, total = before_count
                if self.march_slots_full(before_status):
                    self.game_logger.info("All march slots are busy. Ending gather loop.")
                    self.adb_tap(*context.CONFIG["action_coords"]["open_world"])  # Close world view
                    self.confirm_screen(must_screen="home", timeout=3.0, where="after closing world with all troops busy")
                    self.all_troops_busy = True
                    self._obs_event(
                        "gather_done",
                        game=game_name,
                        reason="all_troops_busy",
                        attempt=attempt,
                        used=used,
                        total=total,
                        march_status=self.format_march_sidebar(before_status),
                    )
                    self._reset_stuck(game_name, "march_dispatch_not_confirmed")
                    self._record_action(
                        game_name,
                        "gathering",
                        "unavailable",
                        "All march slots are busy",
                        used=used,
                        total=total,
                    )
                    return True

            # If troops are available, proceed to send one
            # Ensure still in world before proceeding
            if not self.confirm_screen(any_of=["hq", "hq2"], none_of=["home"], must_screen="world", timeout=2.0, where="before search_button tap", abort_on_fail=True):
                self._obs_event("gather_abort", game=game_name, reason="left_world_before_search", attempt=attempt)
                return False
            search_panel_open = False
            for open_attempt in range(1, 4):
                self.adb_tap(*context.CONFIG["action_coords"]["search_button"])
                time.sleep(context.CONFIG["timing"]["action_delay"])
                opened_frame = self.adb_screenshot()
                if self._gather_search_panel_visible(opened_frame):
                    search_panel_open = True
                    self.game_logger.info(
                        "Gather search panel confirmed open on attempt %d.",
                        open_attempt,
                    )
                    break
                self.game_logger.warning(
                    "Gather search panel did not open after tap %d/3.",
                    open_attempt,
                )
            if not search_panel_open:
                self._obs_capture(
                    f"gather_search_panel_open_failed_{game_name}",
                    game=game_name,
                    attempt=attempt,
                )
                self._record_action(
                    game_name,
                    "gathering",
                    "failed",
                    "Gather search panel did not open",
                )
                self.ensure_base_view()
                return False

            resources = ["Food", "Wood", "Zent"]
            weights = [50, 50, 0]
            resource = random.choices(resources, weights=weights, k=1)[0]

            if self.search_and_gather_resource(resource):
                self.game_logger.info(f"Successfully found and selected {resource}")
            else:
                self.game_logger.warning(f"Failed to find {resource}; returning to base before retrying.")
                self._obs_event("gather_resource_not_found", game=game_name, attempt=attempt, resource=resource)
                if self._note_stuck(game_name, "resource_not_found"):
                    self.recover_current_game(game_name, "resource_not_found")
                    return False
                self.ensure_base_view()
                continue
            self._reset_stuck(game_name, "resource_not_found")

            # The resource and level are selected while the search panel is
            # still open. Press Search first, then require the resulting node
            # view before interacting with the mine.
            resource_search_started = False
            for search_attempt in range(1, 4):
                self.adb_tap(*context.CONFIG["action_coords"]["gather_search"])
                time.sleep(context.CONFIG["timing"]["action_delay"])
                searched_frame = self.adb_screenshot()
                if (
                    not self._gather_search_panel_visible(searched_frame)
                    and self.is_screen("world", searched_frame)
                ):
                    resource_search_started = True
                    self.game_logger.info(
                        "Resource Search tap confirmed on attempt %d.",
                        search_attempt,
                    )
                    break
                self.game_logger.warning(
                    "Resource Search tap %d/3 left the gather panel open.",
                    search_attempt,
                )
            if not resource_search_started:
                self._obs_capture(
                    f"gather_resource_search_tap_failed_{game_name}",
                    game=game_name,
                    attempt=attempt,
                    resource=resource,
                )
                self._obs_event("gather_abort", game=game_name, reason="resource_search_failed", attempt=attempt)
                self._record_action(
                    game_name,
                    "gathering",
                    "failed",
                    "Resource Search button did not close the gather panel",
                    resource=resource,
                )
                self.ensure_base_view()
                return False
            self.adb_tap(*context.CONFIG["action_coords"]["middle_screen"])
            time.sleep(context.CONFIG["timing"]["action_delay"])
            self.adb_tap(*context.CONFIG["action_coords"]["gather_button"])
            time.sleep(context.CONFIG["timing"]["action_delay"])

            march_tapped = False
            dispatch_frame = self.adb_screenshot()
            capacity = context._ocr_troop_capacity(
                dispatch_frame,
                tuple(context.CONFIG.get("troop_capacity_value_rois", ())),
            )
            if capacity is None or capacity[0] <= 0:
                reason = (
                    "Troop Capacity OCR failed"
                    if capacity is None
                    else f"no healthy trained troops selected ({capacity[0]}/{capacity[1]})"
                )
                self.game_logger.info(
                    "[%s] Skipping gathering dispatch: %s.",
                    game_name,
                    reason,
                )
                self._record_action(
                    game_name,
                    "gathering",
                    "unavailable",
                    reason,
                )
                self._obs_capture(
                    f"gather_troop_capacity_unavailable_{game_name}",
                    image=dispatch_frame,
                    game=game_name,
                    reason=reason,
                )
                self.ensure_base_view()
                return False
            for march_attempt in range(1, 4):
                march_button = self._locate_gather_march_button(dispatch_frame)
                if march_button is None:
                    if march_attempt == 1:
                        self.game_logger.warning(
                            "Gather node did not open a troop dispatch popup."
                        )
                    break

                self.game_logger.info(
                    "Clicking visible March button at %s (attempt %d/3).",
                    march_button,
                    march_attempt,
                )
                self.adb_tap(*march_button)
                time.sleep(context.CONFIG["timing"]["action_delay"])
                dispatch_frame = self.adb_screenshot()
                if self._locate_gather_march_button(dispatch_frame) is None:
                    march_tapped = True
                    self.game_logger.info(
                        "March button click confirmed; dispatch popup closed."
                    )
                    break
                self.game_logger.warning(
                    "March dispatch popup remained open after tap %d/3.",
                    march_attempt,
                )

            if not march_tapped:
                self._obs_capture(
                    f"gather_march_button_failed_{game_name}",
                    image=dispatch_frame,
                    game=game_name,
                    attempt=attempt,
                )
                self._record_action(
                    game_name,
                    "gathering",
                    "failed",
                    "March button was not visible or did not close the dispatch popup",
                    resource=resource,
                )
                self.ensure_base_view()
                continue

            time.sleep(context.CONFIG["timing"]["action_delay"])
            after_status = self.read_march_status(where=f"gather attempt {attempt} after dispatch")
            after_count = self.march_count(after_status)
            if before_count and after_count:
                before_used, before_total = before_count
                after_used, after_total = after_count
                dispatch_ok, dispatch_reason = self.march_dispatch_confirmed(before_status, after_status)
                if not dispatch_ok:
                    self.game_logger.warning(
                        "Gather dispatch not confirmed by march sidebar (%s): before=%s after=%s",
                        dispatch_reason,
                        self.format_march_sidebar(before_status),
                        self.format_march_sidebar(after_status),
                    )
                    self._obs_event(
                        "gather_dispatch_unconfirmed",
                        game=game_name,
                        attempt=attempt,
                        before=f"{before_used}/{before_total}",
                        after=f"{after_used}/{after_total}",
                        before_status=self.format_march_sidebar(before_status),
                        after_status=self.format_march_sidebar(after_status),
                        reason=dispatch_reason,
                    )
                    if self._note_stuck(game_name, "march_dispatch_not_confirmed"):
                        self.recover_current_game(game_name, "march_dispatch_not_confirmed")
                        self._record_action(
                            game_name,
                            "gathering",
                            "failed",
                            "March dispatch could not be confirmed",
                            reason=dispatch_reason,
                        )
                        return False
                    self.ensure_base_view()
                    continue
                self.game_logger.info(
                    "Gather dispatch confirmed by march sidebar (%s): before=%s after=%s",
                    dispatch_reason,
                    self.format_march_sidebar(before_status),
                    self.format_march_sidebar(after_status),
                )
                self._record_action(
                    game_name,
                    "gathering",
                    "success",
                    f"{resource} gathering march sent",
                    resource=resource,
                    confirmation=dispatch_reason,
                    before=f"{before_used}/{before_total}",
                    after=f"{after_used}/{after_total}",
                )
                self._last_gather_dispatches += 1
                if self.march_slots_full(after_status):
                    self.all_troops_busy = True
                self._reset_stuck(game_name, "march_dispatch_not_confirmed")
            elif before_count:
                before_used, before_total = before_count
                self.game_logger.warning(
                    "Could not parse march sidebar after dispatch; before=%s",
                    self.format_march_sidebar(before_status),
                )
                self._obs_event(
                    "gather_dispatch_after_status_unknown",
                    game=game_name,
                    attempt=attempt,
                    before=f"{before_used}/{before_total}",
                    before_status=self.format_march_sidebar(before_status),
                )

            # Handle radar
            if not self.do_radar(game_name=game_name):
                # Radar is post-dispatch housekeeping. Do not discard a
                # confirmed gather because its optional cleanup screen changed.
                self._abort_cycle = False
                self.game_logger.warning(
                    "Radar cleanup failed after gather dispatch; continuing from base."
                )

            # Back to base between attempts
            self.ensure_base_view()
            self.confirm_screen(must_screen="home", timeout=3.0, where="between gather attempts")
            # Optional: handle trucks after each send (kept as before; guarded by its own cooldowns)
            self.do_trucks(game_name)

        # Max attempts reached; not full
        self.game_logger.info("Reached max gather attempts; troops not full.")
        self.all_troops_busy = False
        self._obs_event("gather_done", game=game_name, reason="max_attempts_reached", max_attempts=max_attempts)
        self._record_action(game_name, "gathering", "failed", "Maximum gather attempts reached")
        return False
