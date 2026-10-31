"""Construction services extracted from the application facade."""
import cv2
import numpy as np
import time
import re
from bot.context import context


def _construction_shortage_controls(frame, templates):
    title = context._template_match_centers(frame, templates.get("construction_get_more_title"), (250, 250, 850, 450), threshold=.9, max_matches=1)
    button = context._template_match_centers(frame, templates.get("construction_replenish_all"), (200, 1500, 900, 1950), threshold=.9, max_matches=1)
    return button[0][:2] if title and button else None


def handle_construction_resource_shortage(self, frame: np.ndarray | None) -> str | None:
    """Resolve the Builder's insufficient-resources prompt conservatively.

    Returns ``"replenished"`` after choosing Replenish All, ``"skipped"``
    after abandoning the upgrade, or ``None`` when the supplied frame is not
    this specific prompt.  Replenish All is the configured default; Skip is
    used only when it is disabled, unavailable, or leaves the same prompt on
    screen (for example, the inventory cannot cover the shortfall).
    """
    if frame is None:
        return None
    roi = tuple(context.CONFIG.get("construction_shortage_prompt_roi", (60, 250, 1020, 1950)))
    prompt_text = context._ocr_frame_text(frame, roi, psm=11)
    visual_replenish = _construction_shortage_controls(frame, self.templates)
    if not context._is_construction_resource_shortage_prompt(prompt_text):
        # Sparse OCR drops the title or merges the button words on this UI.
        title = context._ocr_frame_text(frame, (300, 250, 850, 430), psm=7)
        footer = context._ocr_frame_text(frame, (200, 1600, 900, 1900), psm=6)
        prompt_text = title + " " + footer
    if not visual_replenish and not context._is_construction_resource_shortage_prompt(prompt_text):
        return None

    self.game_logger.info("Insufficient construction resources detected: %s", prompt_text.replace("\n", " | "))
    is_get_more_screen = bool(visual_replenish) or "getmore" in re.sub(r"[^a-z]", "", prompt_text.lower())
    replenish_point = visual_replenish or context._find_ocr_phrase_center(frame, "replenish all", roi)
    if replenish_point is None:
        replenish_point = context._find_ocr_word_center(frame, "replenish", roi)

    if context.CONFIG.get("construction_replenish_all_enabled", True) and replenish_point is not None:
        self.game_logger.info(
            "Replenishing construction resources from inventory at (%d, %d).",
            replenish_point[0], replenish_point[1],
        )
        self.adb_tap(*replenish_point)
        time.sleep(context.CONFIG["timing"]["action_delay"])
        after_replenish = self.adb_screenshot()
        after_text = context._ocr_frame_text(after_replenish, roi, psm=11)
        insufficient = context._template_match_centers(
            after_replenish, self.templates.get("construction_replenish_insufficient"),
            (80, 500, 1000, 800), threshold=.9, max_matches=1,
        )
        compact_after = re.sub(r"[^a-z]", "", after_text.lower())
        if insufficient or ("allresources" in compact_after and "wontmeettherequirements" in compact_after):
            self.game_logger.info("Inventory cannot cover this upgrade; cancelling without consuming packs.")
            self._obs_capture("construction_inventory_insufficient", image=after_replenish)
            self.adb_keyevent(4)
            time.sleep(context.CONFIG["timing"]["action_delay"])
            self.adb_keyevent(4)
            self._obs_event("construction_resource_shortage", outcome="skipped_inventory_insufficient")
            return "skipped"
        # Verified game flow: Get More -> Replenish All -> confirmation that
        # lists consumed packs -> original building panel -> Upgrade.
        if is_get_more_screen and context._is_construction_replenish_confirmation(after_text):
            confirm_point = context._find_ocr_word_center(after_replenish, "confirm", roi)
            if confirm_point is None:
                self.game_logger.warning("Replenishment confirmation was shown, but Confirm was not readable.")
                self._obs_capture("construction_replenish_confirm_missing", image=after_replenish)
                return None
            self.game_logger.info(
                "Confirming inventory-pack replenishment at (%d, %d).",
                confirm_point[0], confirm_point[1],
            )
            self.adb_tap(*confirm_point)
            time.sleep(context.CONFIG["timing"]["action_delay"])
            building_frame = self.adb_screenshot()
            upgrade_point = context._find_ocr_word_center(building_frame, "upgrade", (500, 1250, 1050, 2150))
            if upgrade_point is None:
                self.game_logger.warning("Resources replenished, but the final building Upgrade button was not readable.")
                self._obs_capture("construction_replenished_upgrade_missing", image=building_frame)
                return None
            self.game_logger.info(
                "Starting replenished building upgrade at (%d, %d).",
                upgrade_point[0], upgrade_point[1],
            )
            self.adb_tap(*upgrade_point)
            time.sleep(context.CONFIG["timing"]["action_delay"])
            self._obs_event("construction_resource_shortage", outcome="replenished")
            return "replenished"
        if not context._is_construction_resource_shortage_prompt(after_text):
            self._obs_event("construction_resource_shortage", outcome="replenished")
            return "replenished"
        # Some game versions treat Replenish All as a selection and keep a
        # separate confirmation button in the same dialog.  Confirm it before
        # deciding that the inventory cannot cover the upgrade.
        confirm_point = context._find_ocr_word_center(after_replenish, "confirm", roi)
        if confirm_point is not None:
            self.game_logger.info(
                "Confirming replenished construction at (%d, %d).",
                confirm_point[0], confirm_point[1],
            )
            self.adb_tap(*confirm_point)
            time.sleep(context.CONFIG["timing"]["action_delay"])
            confirmed_frame = self.adb_screenshot()
            confirmed_text = context._ocr_frame_text(confirmed_frame, roi, psm=11)
            if not context._is_construction_resource_shortage_prompt(confirmed_text):
                self._obs_event("construction_resource_shortage", outcome="replenished")
                return "replenished"
            after_replenish = confirmed_frame
        frame = after_replenish
        self.game_logger.warning("Replenish All did not resolve the resource shortage; skipping construction.")
    elif context.CONFIG.get("construction_replenish_all_enabled", True):
        self.game_logger.warning("Resource shortage prompt found, but Replenish All was not readable; skipping construction.")

    skip_point = context._find_ocr_phrase_center(frame, "skip construction", roi)
    if skip_point is None:
        skip_point = context._find_ocr_word_center(frame, "skip", roi)
    if skip_point is None:
        if is_get_more_screen:
            self.game_logger.info("Closing Get More because replenishment cannot be completed.")
            self.adb_keyevent(4)
            time.sleep(context.CONFIG["timing"]["action_delay"])
            self._obs_event("construction_resource_shortage", outcome="skipped")
            return "skipped"
        self.game_logger.warning("Resource shortage prompt found, but Skip was not readable; leaving it untouched.")
        self._obs_capture("construction_resource_shortage_unresolved", image=frame)
        return None

    self.game_logger.info("Skipping construction due to insufficient resources at (%d, %d).", skip_point[0], skip_point[1])
    self.adb_tap(*skip_point)
    time.sleep(context.CONFIG["timing"]["action_delay"])
    self._obs_event("construction_resource_shortage", outcome="skipped")
    return "skipped"


def _builder_queue_is_open(frame, templates):
    """Recognize the Builder dialog independently of worker availability."""
    return bool(context._template_match_centers(
        frame, templates.get("builder_queue_title"), (250, 200, 850, 800),
        threshold=0.88, max_matches=1,
    ))


def _available_builder_count(frame, template):
    if frame is None or template is None:
        return None
    remaining = frame.copy()
    count = 0
    for _ in range(6):
        match = context._locate_available_builder_button(remaining, template)
        if match is None:
            break
        x, y, _ = match
        count += 1
        remaining[max(0,y-70):y+70,max(0,x-100):x+100] = 0
    return count


def open_builder_queue(self, game_name: str | None = None):
    """Open the visually located hardhat and verify the dialog before scanning."""
    cfg = context.CONFIG.get("builder_navigation", {})
    for attempt in range(max(1, int(cfg.get("max_attempts", 3)))):
        frame = self.adb_screenshot()
        if context._builder_queue_is_open(frame, self.templates):
            return frame
        hits = context._template_match_centers(
            frame, self.templates.get("builder_hardhat"), (0, 200, 150, 700),
            threshold=0.88, max_matches=1,
        )
        if not hits:
            self.game_logger.warning("Builder hardhat was not visible on attempt %d.", attempt + 1)
            break
        self.game_logger.info("Opening Builder queue via hardhat at %s (attempt %d).", hits[0][:2], attempt + 1)
        self.adb_tap(*hits[0][:2])
        deadline = time.monotonic() + float(cfg.get("open_timeout", 3.0))
        while time.monotonic() < deadline:
            time.sleep(0.5)
            frame = self.adb_screenshot()
            if context._builder_queue_is_open(frame, self.templates):
                self.game_logger.info("Builder queue opening confirmed.")
                return frame
        self.game_logger.warning("Builder queue did not open; retrying with a fresh HUD match.")
    self._obs_capture("builder_queue_open_failed", image=frame, game=game_name or "unknown")
    self._record_action(game_name or "unknown", "construction_navigation", "failed", "Builder queue did not open")
    return None


def do_build(self, game_name: str | None = None):
        """Start the builder's recommended upgrade and request alliance help."""
        self.game_logger.info("Checking for an available builder.")
        if not self.ensure_base_view():
            self.game_logger.warning("Unable to recover base screen before construction.")
            self._record_action(game_name or "unknown", "construction", "failed", "Base view unavailable")
            return False

        # The hardhat opens the Builder queue.  Only the green Build button is
        # actionable; blue Speed Up and orange Buy entries are intentionally ignored.
        queue_frame = self.open_builder_queue(game_name)
        if queue_frame is None:
            self.game_logger.warning("Construction skipped because the Builder queue could not be opened.")
            self._record_action(game_name or "unknown", "construction", "failed", "Builder queue navigation failed")
            self.ensure_base_view()
            return False
        # An occupied worker can be listed first with a blue Speed Up control.
        # Scan all worker rows, including a free worker in the first row.
        build_match = context._locate_available_builder_button(
            queue_frame,
            self.templates.get("builder_build"),
        )
        free_before = _available_builder_count(queue_frame, self.templates.get("builder_build"))
        if build_match is None:
            self.game_logger.info("Builder queue confirmed, but no green Build action is available.")
            self._record_action(game_name or "unknown", "construction", "blocked", "No free builder is available")
            self._obs_capture("builder_build_unavailable", image=queue_frame, game=game_name or "unknown")
            self.ensure_base_view()
            return False

        build_x, build_y, build_score = build_match
        self.game_logger.info(
            "Clicking available Builder action at (%d, %d), score %.4f.",
            build_x,
            build_y,
            build_score,
        )
        self.adb_tap(build_x, build_y)

        upgrade_name = None
        upgrade_point = None
        upgrade_frame = None
        # Recommended buildings can expose either a four-action radial menu
        # or a three-action glowing/tutorial menu.  Match only the radial-menu
        # band with exact-scale CCOEFF: this is both faster and more tolerant
        # of the animated yellow glow than the general full-screen matcher.
        ux1, uy1, ux2, uy2 = (250, 1000, 850, 1400)
        upgrade_click_y_offsets = {
            "builder_upgrade_menu": 115,
            "builder_upgrade_menu_glow": 120,
        }
        upgrade_match_thresholds = {
            "builder_upgrade_menu": 0.86,
            # The glow and tutorial hand are animated.  Observed valid scores
            # range from 0.77 to 1.00, while pre-menu frames stay below 0.50.
            "builder_upgrade_menu_glow": 0.70,
        }

        def locate_builder_upgrade(frame):
            if frame is None:
                return None, None
            green_point = context._locate_green_builder_upgrade(frame)
            if green_point is not None:
                self.image_logger.debug(
                    "Found green builder Upgrade control at (%d, %d).",
                    green_point[0],
                    green_point[1],
                )
                return "green_upgrade_control", green_point

            radial_roi = frame[uy1:uy2, ux1:ux2]
            for template_name in upgrade_click_y_offsets:
                template = self.templates.get(template_name)
                if template is None:
                    continue
                template_bgr = template[:, :, :3] if template.ndim == 3 else template
                if (
                    radial_roi.shape[0] < template_bgr.shape[0]
                    or radial_roi.shape[1] < template_bgr.shape[1]
                ):
                    continue
                result = cv2.matchTemplate(radial_roi, template_bgr, cv2.TM_CCOEFF_NORMED)
                _, score, _, location = cv2.minMaxLoc(result)
                if score >= upgrade_match_thresholds[template_name]:
                    self.image_logger.debug(
                        "Found '%s' in builder radial ROI (CCOEFF=%.4f).",
                        template_name,
                        score,
                    )
                    return template_name, (
                        ux1 + location[0] + template.shape[1] // 2,
                        uy1 + location[1] + upgrade_click_y_offsets[template_name],
                    )
            return None, None

        deadline = time.time() + 6.0
        while time.time() < deadline:
            time.sleep(0.25)
            upgrade_frame = self.adb_screenshot()
            upgrade_name, upgrade_point = locate_builder_upgrade(upgrade_frame)
            if upgrade_point is not None:
                break
        if upgrade_point is None:
            self.game_logger.warning("Build opened, but the recommended building Upgrade was not found.")
            self._record_action(game_name or "unknown", "construction", "failed", "Recommended Upgrade action not found")
            self._obs_capture("builder_upgrade_menu_missing", image=upgrade_frame)
            self.ensure_base_view()
            return False

        upgrade_x, upgrade_y = upgrade_point
        self.game_logger.info(
            "Clicking recommended building Upgrade (%s) at (%d, %d).",
            upgrade_name,
            upgrade_x,
            upgrade_y,
        )
        self.adb_tap(upgrade_x, upgrade_y)
        time.sleep(context.CONFIG["timing"]["action_delay"])

        confirm_frame = self.adb_screenshot()
        self._obs_capture("builder_upgrade_dialog", image=confirm_frame, game=game_name)
        confirm_loc = self.find_template("builder_upgrade_confirm", confirm_frame, click=False)
        if (
            confirm_loc is None
            and locate_builder_upgrade(confirm_frame)[1] is not None
        ):
            # A one-time tutorial hand can consume the first Upgrade tap.
            self.game_logger.info("Upgrade tutorial overlay consumed the tap; retrying once.")
            self.adb_tap(upgrade_x, upgrade_y)
            time.sleep(context.CONFIG["timing"]["action_delay"])
            confirm_frame = self.adb_screenshot()
            confirm_loc = self.find_template("builder_upgrade_confirm", confirm_frame, click=False)
        if confirm_loc is None:
            self.game_logger.warning("Building Upgrade dialog did not open.")
            self._record_action(game_name or "unknown", "construction", "failed", "Upgrade dialog did not open")
            self._obs_capture("builder_upgrade_confirm_missing", image=confirm_frame)
            self.ensure_base_view()
            return False

        confirm_tpl = self.templates["builder_upgrade_confirm"]
        confirm_x = confirm_loc[0] + confirm_tpl.shape[1] // 2
        confirm_y = confirm_loc[1] + min(115, confirm_tpl.shape[0] - 5)
        actual_upgrade = context._find_ocr_word_center(confirm_frame, "upgrade", (500, 1400, 1050, 1900))
        if actual_upgrade is not None:
            confirm_x, confirm_y = actual_upgrade
        self.game_logger.info("Confirming building Upgrade at (%d, %d).", confirm_x, confirm_y)
        self.adb_tap(confirm_x, confirm_y)
        time.sleep(context.CONFIG["timing"]["action_delay"])

        started_frame = self.adb_screenshot()
        resource_shortage_outcome = self.handle_construction_resource_shortage(started_frame)
        if resource_shortage_outcome == "skipped":
            self._record_action(game_name or "unknown", "construction", "blocked", "Insufficient inventory resources; construction skipped")
            self.game_logger.info("Construction skipped because inventory could not cover its resource cost.")
            self.ensure_base_view()
            return False
        if resource_shortage_outcome == "replenished":
            # Replenish All completes the pending construction request. Take a
            # fresh frame before testing for the usual started-job handshake.
            started_frame = self.adb_screenshot()
        prompt_text = context._ocr_frame_text(started_frame, tuple(context.CONFIG["construction_shortage_prompt_roi"]), psm=11)
        if context._is_construction_resource_shortage_prompt(prompt_text) or context._is_construction_replenish_confirmation(prompt_text):
            self._record_action(game_name or "unknown", "construction", "blocked", "Resource replenishment remains unresolved")
            self.ensure_base_view()
            return False
        if self.find_template("builder_upgrade_confirm", started_frame, click=False) is not None:
            self.game_logger.warning("Upgrade confirmation is still visible; construction did not start.")
            self._record_action(game_name or "unknown", "construction", "failed", "Upgrade confirmation remained visible")
            self._obs_capture("builder_start_unconfirmed", image=started_frame)
            self.ensure_base_view()
            return False

        self.game_logger.info("Upgrade requested; checking construction outcome.")

        # The newly started job remains centred and displays a handshake pin.
        # Keep the ROI narrow so unrelated help bubbles elsewhere on the base
        # cannot be mistaken for this construction request.
        hx1, hy1, hx2, hy2 = (430, 790, 610, 990)
        help_loc = self.find_template(
            "builder_construction_help",
            started_frame[hy1:hy2, hx1:hx2],
            click=False,
        )
        if help_loc is not None:
            help_tpl = self.templates["builder_construction_help"]
            help_point = (
                hx1 + help_loc[0] + help_tpl.shape[1] // 2,
                hy1 + help_loc[1] + help_tpl.shape[0] // 2,
            )
        else:
            help_point = context._locate_builder_help_pin(started_frame)

        if help_point is None:
            self.game_logger.info("No construction-help handshake; verifying worker occupancy instead.")
            self._obs_capture("builder_help_missing", image=started_frame)
            self.ensure_base_view()
            after_queue = self.open_builder_queue(game_name)
            free_after = _available_builder_count(after_queue, self.templates.get("builder_build"))
            if free_before is None or free_after is None or free_after >= free_before:
                self._record_action(game_name or "unknown", "construction", "failed", "Upgrade did not consume a free builder")
                self.ensure_base_view()
                return False
        else:
            help_x, help_y = help_point
            self.game_logger.info("Requesting alliance construction help at (%d, %d).", help_x, help_y)
            self.adb_tap(help_x, help_y)
            time.sleep(context.CONFIG["timing"]["action_delay"])
            helped_frame = self.adb_screenshot()
            if helped_frame is None:
                self._record_action(game_name or "unknown", "construction_help", "failed", "Help verification screenshot unavailable")
                self.ensure_base_view()
                return False
            still_visible_template = self.find_template(
                "builder_construction_help",
                helped_frame[hy1:hy2, hx1:hx2],
                click=False,
            )
            still_visible = (
                still_visible_template is not None
                or context._locate_builder_help_pin(helped_frame) is not None
            )
            if not still_visible:
                self.game_logger.info("Alliance construction help request confirmed.")
            else:
                self.game_logger.warning("Construction handshake remained after the help request.")
                self._obs_capture("builder_help_unconfirmed", image=helped_frame)

        self.ensure_base_view()
        self._record_action(game_name or "unknown", "construction", "success", "Building upgrade confirmed by construction handshake or worker occupancy")
        return True
