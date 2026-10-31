"""Shop services extracted from the application facade."""
import cv2
import numpy as np
import time
from difflib import SequenceMatcher
import re
from bot.context import context


def do_alliance_shop_badges(self, game_name: str) -> bool:
        """Buy one configured weekly-capped Alliance Shop product.

        The shop changes its ordering and keeps a partially visible row under
        its header.  Probe a scrolling grid and trust only the purchase-dialog
        title.  A Buy tap is *not* a purchase: success requires the game's
        Congratulations overlay, which is also captured for troubleshooting.
        """
        cfg = context.CONFIG.get("alliance_shop_badges", {})
        limit = int(cfg.get("weekly_bundle_limit", 10))
        template_name = str(cfg.get("product_template", "")).strip()
        if not cfg.get("enabled", False) or limit < 1:
            return False
        if not template_name or template_name not in self.templates:
            self._record_action(
                game_name, "alliance_shop_badges", "failed",
                "No item-art template configured for this Alliance Shop product",
            )
            return False
        if not self.ensure_base_view(timeout=30.0, max_esc=10):
            return False
        self.adb_tap(*context.CONFIG["action_coords"]["alliance"])
        time.sleep(context.CONFIG["timing"]["action_delay"])
        self.adb_tap(*context.CONFIG["action_coords"]["alliance_shop"])
        time.sleep(context.CONFIG["timing"]["action_delay"])
        # The catalogue is scrollable and regularly re-ordered.  Find every
        # visible instance of the configured item art, then identify the exact
        # product from the purchase-dialog title.  No card positions are used.
        def template_hits(frame):
            template = self.templates.get(template_name)
            if frame is None or template is None:
                return []
            x1, y1, x2, y2 = (int(v) for v in cfg.get("scan_roi", (45, 790, 1035, 1900)))
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                return []
            source = cv2.cvtColor(crop[:, :, :3], cv2.COLOR_BGR2GRAY)
            artwork = template[:, :, :3] if len(template.shape) == 3 else template
            artwork = cv2.cvtColor(artwork, cv2.COLOR_BGR2GRAY) if len(artwork.shape) == 3 else artwork
            threshold = float(cfg.get("template_threshold", 0.88))
            candidates = []
            # Small scale tolerance handles the Android display density while
            # retaining enough detail that unrelated blue cards are rejected.
            for scale in (0.90, 0.95, 1.00, 1.05, 1.10):
                scaled = cv2.resize(artwork, None, fx=scale, fy=scale,
                                    interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
                if scaled.shape[0] > source.shape[0] or scaled.shape[1] > source.shape[1]:
                    continue
                matches = cv2.matchTemplate(source, scaled, cv2.TM_CCOEFF_NORMED)
                ys, xs = np.where(matches >= threshold)
                for match_y, match_x in zip(ys, xs):
                    candidates.append((float(matches[match_y, match_x]),
                                       x1 + int(match_x + scaled.shape[1] / 2),
                                       y1 + int(match_y + scaled.shape[0] / 2)))
            # Non-maximum suppression: multiple scales often find one icon.
            selected = []
            for score, center_x, center_y in sorted(candidates, reverse=True):
                if all((center_x - old_x) ** 2 + (center_y - old_y) ** 2 > 90 ** 2
                       for _, old_x, old_y in selected):
                    selected.append((score, center_x, center_y))
            # Shield variants share most pixels.  An 8h icon must not inherit
            # the 24h card's sold-out status (or vice versa). Require the
            # requested template to beat the other duration's artwork.
            verified = []
            shield_templates = ("alliance_shop_peace_shield", "alliance_shop_peace_shield_24h")
            for score, x, y in selected:
                competing_score = -1.0
                if template_name in shield_templates:
                    nearby = frame[max(790, y - 140):min(1900, y + 140),
                                   max(45, x - 140):min(1035, x + 140)]
                    nearby = cv2.cvtColor(nearby[:, :, :3], cv2.COLOR_BGR2GRAY)
                    for other_name in shield_templates:
                        if other_name == template_name or other_name not in self.templates:
                            continue
                        other = self.templates[other_name]
                        other = cv2.cvtColor(other[:, :, :3], cv2.COLOR_BGR2GRAY) if len(other.shape) == 3 else other
                        for scale in (0.90, 0.95, 1.00, 1.05, 1.10):
                            resized = cv2.resize(other, None, fx=scale, fy=scale)
                            if resized.shape[0] <= nearby.shape[0] and resized.shape[1] <= nearby.shape[1]:
                                competing_score = max(competing_score, float(cv2.minMaxLoc(
                                    cv2.matchTemplate(nearby, resized, cv2.TM_CCOEFF_NORMED))[1]))
                if score >= competing_score:
                    verified.append((x, y))
            return verified

        # Blank product_name is allowed for an explicitly enabled entry whose
        # artwork is known but whose localized dialog name has not yet been
        # catalogued.  In that case bind the transaction to the title read
        # from that exact template match before any Buy tap.
        target_name = str(cfg.get("product_name", "badge")).lower().strip()
        success = False
        purchase_seen = False
        for scroll_no in range(int(cfg.get("max_scrolls", 5)) + 1):
            frame = self.adb_screenshot()
            if scroll_no == 0:
                reset_text = context._ocr_frame_text(frame, tuple(context.CONFIG["alliance_shop_catalog"].get("reset_countdown_roi", (0, 250, 1080, 790))), psm=6)
                reset_seconds = context._parse_shop_reset_seconds(reset_text)
                if reset_seconds is not None:
                    if not hasattr(self, "_shop_reset_ts"):
                        self._shop_reset_ts = {}
                    self._shop_reset_ts[game_name] = time.time() + reset_seconds + 60
            hits = template_hits(frame)
            self.game_logger.info(
                "Alliance Shop template %s found %d candidate(s), view %d/%d.",
                template_name, len(hits), scroll_no + 1, int(cfg.get("max_scrolls", 5)) + 1,
            )
            if frame is not None:
                self._obs_capture("alliance_shop_template_scan", image=frame,
                                  game=game_name, product=target_name, candidates=len(hits))
            for point in hits:
                price_button = context._alliance_shop_price_button(frame, point)
                if price_button is None:
                    limit_text = context._ocr_frame_text(
                        frame,
                        (230 if point[0] < 540 else 710, max(790, point[1] - 90),
                         520 if point[0] < 540 else 1005, point[1] + 90),
                        psm=6,
                    )
                    limit_match = re.search(r"(\d+)\s*/\s*(\d+)", limit_text)
                    limit_reached = bool(limit_match and int(limit_match[2]) > 0
                                         and int(limit_match[1]) >= int(limit_match[2]))
                    footer = context._ocr_frame_text(
                        frame,
                        (75 if point[0] < 540 else 570, point[1] + 180,
                         510 if point[0] < 540 else 990, min(point[1] + 280, 1960)),
                        psm=7,
                    ).lower()
                    # Outlined lettering commonly reads as SoldiOutiThisWeek.
                    # This is only considered when there is no gold Buy footer.
                    footer_letters = re.sub(r"[^a-z]", "", footer)
                    sold_out = SequenceMatcher(None, footer_letters, "soldoutthisweek").ratio() >= 0.80
                    if not limit_reached and not sold_out:
                        # The black text's white outline is more legible than
                        # its interior. Isolate that outline on grey footers.
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        outlined = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY)[1]
                        clean_footer = context._ocr_frame_text(
                            cv2.cvtColor(outlined, cv2.COLOR_GRAY2BGR),
                            (75 if point[0] < 540 else 570, point[1] + 180,
                             510 if point[0] < 540 else 990, min(point[1] + 280, 1960)), psm=7,
                        )
                        sold_out = SequenceMatcher(None, re.sub(r"[^a-z]", "", clean_footer.lower()),
                                                   "soldoutthisweek").ratio() >= 0.80
                    if limit_reached or sold_out:
                        self.game_logger.info("%s already sold out this week; weekly limit satisfied.", target_name)
                        self._record_action(game_name, "alliance_shop_badges", "skipped",
                                            f"{target_name}: weekly purchase limit already reached")
                        self.adb_keyevent(111)
                        self.ensure_base_view()
                        return True
                    self.game_logger.info("%s artwork found at %s but no visible purchasable price footer (%s).",
                                          target_name, point, footer.strip())
                    continue
                self.game_logger.info("Opening %s via detected price button %s (artwork %s).",
                                      target_name, price_button, point)
                self.adb_tap(*price_button)
                time.sleep(0.7)
                title = self.extract_text_from_roi(300, 520, 780, 690, self.device_id, psm="7")
                normalized_title = re.sub(r"\s+", " ", (title or "").lower()).strip()
                compact_title = re.sub(r"[^a-z0-9]", "", normalized_title)
                compact_target = re.sub(r"[^a-z0-9]", "", target_name)
                if not compact_title or (compact_target and compact_target not in compact_title):
                    self.game_logger.warning("Rejected shop dialog: expected %r, read %r.", target_name, normalized_title)
                    self.adb_tap(945, 490)  # modal close; not an item action
                    continue
                if not target_name:
                    target_name = normalized_title
                purchase_seen = True
                for _ in range(limit - 1):
                    self.adb_tap(*context.CONFIG["action_coords"]["alliance_shop_modal_plus"])
                    time.sleep(0.2)
                self.adb_tap(*context.CONFIG["action_coords"]["alliance_shop_modal_buy"])
                time.sleep(max(1.5, float(context.CONFIG["timing"]["long_delay"])))
                reward_frame = self.adb_screenshot()
                # Read the heading and item label separately. The animated
                # artwork/barbed-wire decoration breaks broad-block OCR even
                # when the purchase really succeeded.
                reward_heading = context._ocr_frame_text(
                    reward_frame, (240, 540, 840, 620), psm=7
                ) if reward_frame is not None else ""
                reward_label = context._ocr_frame_text(
                    reward_frame, (200, 820, 880, 1050), psm=6
                ) if reward_frame is not None else ""
                reward_text = reward_heading + " " + reward_label
                normalized_reward = re.sub(r"[^a-z0-9]+", " ", reward_text.lower())
                expected_item = re.sub(r"[^a-z0-9]+", " ", target_name)
                success = (
                    "congratulations" in normalized_reward
                    and re.sub(r"[^a-z0-9]", "", expected_item)
                    in re.sub(r"[^a-z0-9]", "", normalized_reward)
                )
                self.game_logger.info("%s purchase confirmation: confirmed=%s heading=%r item=%r.",
                                      target_name, success, reward_heading, reward_label)
                if reward_frame is not None:
                    self._obs_capture(
                        "alliance_shop_purchase_confirmed" if success else "alliance_shop_purchase_unconfirmed",
                        image=reward_frame, game=game_name, product=target_name,
                    )
                if success:
                    self.adb_tap(*context.CONFIG["action_coords"]["mail_reward_dismiss"])
                    time.sleep(0.8)
                    break
                # The dialog remains open on a rejected purchase.  Close it
                # before looking at the next card rather than treating it as
                # a completed weekly action.
                self.adb_tap(945, 490)
                time.sleep(0.4)
            if success:
                break
            if scroll_no < int(cfg.get("max_scrolls", 5)):
                self.adb_swipe(*cfg["scroll"], duration_ms=600)
                time.sleep(context.CONFIG["timing"]["action_delay"])
        if success:
            self._record_action(game_name, "alliance_shop_badges", "success",
                                f"Confirmed purchase of {target_name} (up to {limit} weekly bundles)")
        else:
            self._record_action(game_name, "alliance_shop_badges", "failed",
                                (f"{target_name} purchase reward was not confirmed" if purchase_seen
                                 else f"{target_name} card was not found"))
        self.adb_keyevent(111)
        time.sleep(context.CONFIG["timing"]["action_delay"])
        self.ensure_base_view()
        return success


def do_alliance_shop_shields(self, game_name: str) -> bool:
        """Buy weekly 24h and 8h peace shields through the same scanned flow."""
        shield_cfg = context.CONFIG.get("alliance_shop_shields", {})
        base_cfg = context.CONFIG["alliance_shop_badges"]
        original_name = base_cfg.get("product_name")
        original_limit = base_cfg.get("weekly_bundle_limit", 10)
        all_ok = True
        try:
            for product_name, limit in shield_cfg.get("products", ()):
                base_cfg["product_name"] = product_name
                base_cfg["weekly_bundle_limit"] = int(limit)
                all_ok = self.do_alliance_shop_badges(game_name) and all_ok
        finally:
            base_cfg["weekly_bundle_limit"] = original_limit
            if original_name is None:
                base_cfg.pop("product_name", None)
            else:
                base_cfg["product_name"] = original_name
        return all_ok


def do_alliance_shop_catalog(self, game_name: str) -> bool:
        """Purchase only explicitly enabled Alliance Shop catalogue entries."""
        catalog = context.CONFIG.get("alliance_shop_catalog", {})
        base_cfg = context.CONFIG["alliance_shop_badges"]
        old_name, old_limit = base_cfg.get("product_name"), base_cfg.get("weekly_bundle_limit", 10)
        old_template = base_cfg.get("product_template")
        old_enabled = base_cfg.get("enabled", False)
        completed = True
        attempted = False
        try:
            base_cfg["enabled"] = True
            for product in catalog.get("products", ()):
                if not product.get("enabled", False):
                    continue
                template_name = str(product.get("template", "")).strip()
                if not template_name:
                    self._record_action(
                        game_name, "alliance_shop_catalog", "skipped",
                        f"{product.get('label') or product.get('title') or 'unnamed item'} is enabled but has no item-art template",
                    )
                    completed = False
                    continue
                attempted = True
                base_cfg["product_name"] = str(product.get("title", "")).lower()
                base_cfg["weekly_bundle_limit"] = int(product["weekly_limit"])
                base_cfg["product_template"] = template_name
                completed = self.do_alliance_shop_badges(game_name) and completed
        finally:
            base_cfg["enabled"] = old_enabled
            base_cfg["weekly_bundle_limit"] = old_limit
            if old_name is None:
                base_cfg.pop("product_name", None)
            else:
                base_cfg["product_name"] = old_name
            if old_template is None:
                base_cfg.pop("product_template", None)
            else:
                base_cfg["product_template"] = old_template
        result = attempted and completed
        self._record_action(game_name, "alliance_shop_catalog", "success" if result else "failed",
                            "Enabled items purchased or weekly limits satisfied" if result else "One or more enabled items remain unresolved")
        reset_at = getattr(self, "_shop_reset_ts", {}).get(game_name)
        delay = reset_at - time.time() if result and reset_at else float(catalog.get("check_interval", 21600) if result else catalog.get("retry_interval", 900))
        self._schedule_check(f"alliance_shop_catalog_{game_name}", delay)
        return result
