"""Research services extracted from the application facade."""
import numpy as np
import time
from bot.context import context


def do_research(self, game_name: str | None = None):
        """
        Start a free research item if one is available.

        Sequence
        --------
        1. ensure_base_view().
        2. Look for the "research_free" template on screen.  If not visible,
           no research is available this cycle — return False.
        3. Tap "research_free" to open the research panel.
        4. If a completed research notification appears ("research_complete"),
           collect it.
        5. Tap "research_recommended" to start the suggested next research.
        6. Confirm the research start via the detected Research button.
        7. If the bottom handshake is available, open Research Queue, click
           its blue Help button, and confirm it changes to Speed Up.
        8. Return to a verified base view.

        Returns
        -------
        bool
            True if any research-related action was performed, False if the
            research button was not visible.
        """
        if not self.ensure_base_view():
            self.game_logger.warning("Unable to recover base screen before research; aborting.")
            return False
        did_work = False
        if not self.find_template("research_free", self.adb_screenshot(), click=True):
            self.game_logger.info("No research available to start.")
            return False

        self.game_logger.info("Research opened.")
        time.sleep(context.CONFIG["timing"]["long_delay"])

        if self.find_template("research_complete", self.adb_screenshot(), click=True):
            self.game_logger.info("Collected completed research.")
            did_work = True
            time.sleep(context.CONFIG["timing"]["long_delay"])

        recommended_name = None
        recommended_frame = self.adb_screenshot()
        for template_name in ("research_recommended2", "research_recommended"):
            if self.find_template(template_name, recommended_frame, click=True):
                recommended_name = template_name
                break
        if recommended_name is None:
            self.game_logger.warning("No thumbs-up recommended research was found; aborting research.")
            self._obs_capture("research_no_recommended", image=recommended_frame)
            self.ensure_base_view()
            return did_work

        self.game_logger.info("Selected thumbs-up recommended research (%s).", recommended_name)
        time.sleep(context.CONFIG["timing"]["action_delay"])

        detail_frame = self.adb_screenshot()
        if not self.find_template("research_confirm", detail_frame, click=True):
            self.game_logger.warning("Recommended research opened, but the Research button was not found.")
            self._obs_capture("research_no_confirm", image=detail_frame)
            self.ensure_base_view()
            return did_work

        time.sleep(context.CONFIG["timing"]["action_delay"])
        confirmation_frame = self.adb_screenshot()
        if self.find_template("research_confirm", confirmation_frame, click=False):
            self.game_logger.warning("Research button is still visible; research start was not confirmed.")
            self._obs_capture("research_start_unconfirmed", image=confirmation_frame)
            self.ensure_base_view()
            return did_work

        self.game_logger.info("Research started successfully from the thumbs-up recommendation.")
        did_work = True

        def research_help_center(frame: np.ndarray | None) -> tuple[int, int] | None:
            if frame is None:
                return None
            x1, y1, x2, y2 = context.CONFIG.get("research_help_roi", (400, 1900, 700, 2140))
            crop_loc = self.find_template("research_help", frame[y1:y2, x1:x2], click=False)
            if crop_loc is not None:
                template = self.templates["research_help"]
                return x1 + crop_loc[0] + template.shape[1] // 2, y1 + crop_loc[1] + template.shape[0] // 2
            # UI event banners can move the handshake out of its usual footer
            # band. Search the full frame before declaring alliance help absent.
            full_loc = self.find_template("research_help", frame, click=False)
            if full_loc is None:
                return None
            template = self.templates["research_help"]
            return full_loc[0] + template.shape[1] // 2, full_loc[1] + template.shape[0] // 2

        help_point = None
        for attempt in range(3):
            frame = confirmation_frame if attempt == 0 else self.adb_screenshot()
            help_point = research_help_center(frame)
            if help_point is not None:
                break
            time.sleep(context.CONFIG["timing"]["fast_click_delay"])

        if help_point is None:
            self.game_logger.info("Research started without a visible alliance-help handshake.")
            self._obs_capture("research_help_missing", image=confirmation_frame)
        else:
            self.game_logger.info("Clicking research handshake Help at (%d, %d).", help_point[0], help_point[1])
            self.adb_tap(*help_point)
            time.sleep(context.CONFIG["timing"]["action_delay"])

            queue_frame = self.adb_screenshot()
            qx1, qy1, qx2, qy2 = context.CONFIG.get("research_alliance_help_roi", (600, 550, 950, 900))
            alliance_help_loc = self.find_template(
                "research_alliance_help",
                queue_frame[qy1:qy2, qx1:qx2],
                click=False,
            )
            if alliance_help_loc is None:
                alliance_help_loc = self.find_template(
                    "research_alliance_help", queue_frame, click=False
                )
                if alliance_help_loc is not None:
                    qx1, qy1 = 0, 0
            if alliance_help_loc is None:
                self.game_logger.warning("Research Queue opened, but its blue Help button was not found.")
                self._obs_capture("research_alliance_help_missing", image=queue_frame)
            else:
                alliance_template = self.templates["research_alliance_help"]
                alliance_help_x = qx1 + alliance_help_loc[0] + alliance_template.shape[1] // 2
                # The masked template isolates the Help lettering near the
                # lower half of the button; tap the button's visual center.
                alliance_help_y = qy1 + alliance_help_loc[1] - 12
                self.game_logger.info(
                    "Requesting alliance research help at (%d, %d).",
                    alliance_help_x,
                    alliance_help_y,
                )
                self.adb_tap(alliance_help_x, alliance_help_y)
                time.sleep(context.CONFIG["timing"]["action_delay"])
                self._invalidate_screenshot()
                helped_frame = self.adb_screenshot()
                speed_up_loc = self.find_template(
                    "research_speed_up",
                    helped_frame[qy1:qy2, qx1:qx2],
                    click=False,
                )
                if speed_up_loc is not None:
                    self.game_logger.info("Alliance research help request confirmed (Speed Up shown).")
                else:
                    self.game_logger.warning("Alliance research Help click was not confirmed.")
                    self._obs_capture("research_alliance_help_unconfirmed", image=helped_frame)

        self.ensure_base_view()
        return did_work
