"""Read/act on the live-observed HQ Buff Info shield panel; disarmed by default."""
import re
import time
import cv2
import pytesseract
from bot.context import context


class ShieldUIError(RuntimeError):
    pass


def shield_hours(text):
    normalized = re.sub(r"\s+", " ", text.lower())
    if not re.search(r"peace\s*shield", normalized):
        return None
    values = set(int(value) for value in re.findall(r"(?<!\d)(8|24)\s*(?:h(?:ours?)?|hours?)\b", normalized))
    return next(iter(values)) if len(values) == 1 else None


def owned_count(text):
    values = re.findall(r"(?:owned|in stock|quantity|have)\s*[:x]?\s*(\d+)\b", text.lower())
    return int(values[0]) if len(values) == 1 else None


def shield_seconds(text):
    """Read one labelled shield countdown, never an unrelated HUD timer."""
    if not re.search(r"peace\s*shield", text, re.I):
        return None
    timers = re.findall(r"(?<!\d)(?:(\d+)\s*d\s*)?(\d{1,2}):(\d{2}):(\d{2})(?!\d)", text, re.I)
    if len(timers) != 1:
        return None
    days, hours, minutes, seconds = timers[0]
    hours, minutes, seconds = int(hours), int(minutes), int(seconds)
    if hours > 24 or minutes > 59 or seconds > 59:
        return None
    return int(days or 0) * 86400 + hours * 3600 + minutes * 60 + seconds


def replacement_prompt(text, hours):
    normalized = re.sub(r"\s+", " ", text.lower())
    if hours not in (8, 24) or any(word in normalized for word in ("purchase", "diamonds", "not enough")):
        return False
    # The live generic dialog omits duration. Its authorization comes from the
    # exact item row selected immediately beforehand, not a generic Confirm tap.
    words = re.sub(r"[^a-z]+", " ", normalized).strip()
    generic = "some buff activated already further activation will replace the current one continue"
    if generic in words:
        return True
    return ("shield" in normalized and shield_hours(normalized) == hours
            and any(word in normalized for word in ("replace", "overwrite", "already active", "already activated"))
            and not any(word in normalized for word in ("purchase", "diamonds", "not enough")))


class BuffShieldUI:
    def __init__(self, bot, cfg):
        self.bot, self.cfg = bot, cfg

    def frame(self):
        self.bot._last_screenshot = None
        frame = self.bot.adb_screenshot()
        if frame is None:
            raise ShieldUIError("Fresh screenshot unavailable")
        return frame

    def text(self, frame, name):
        roi = self.cfg.get(name)
        if not roi:
            raise ShieldUIError("Missing calibrated ROI: " + name)
        return context._ocr_frame_text(frame, tuple(roi), psm=6)

    def tap_text(self, frame, text, roi):
        point = context._find_ocr_phrase_center(frame, text, tuple(roi))
        if point is None:
            raise ShieldUIError("Exact UI label was not found: " + text)
        self.bot.adb_tap(*point)
        time.sleep(float(self.cfg.get("transition_delay", 1.5)))

    def navigate(self):
        if not self.bot.ensure_base_view():
            raise ShieldUIError("Base view was not confirmed")
        steps = self.cfg.get("buff_steps", [])
        if not steps:
            raise ShieldUIError("Buff navigation has not been calibrated")
        for step in steps:
            if "point" in step:
                # Only fixed navigation controls calibrated on this phone;
                # item selection/Use are always anchored to exact row text.
                self.bot.adb_tap(*step["point"])
                time.sleep(float(self.cfg.get("transition_delay", 1.5)))
            elif "template" in step:
                hits = context._template_match_centers(self.frame(), self.bot.templates.get(step["template"]),
                    tuple(step["roi"]), threshold=.9, max_matches=2)
                if len(hits) != 1:
                    raise ShieldUIError("Buff navigation template was missing or ambiguous: " + step["template"])
                self.bot.adb_tap(*hits[0][:2])
                time.sleep(float(self.cfg.get("transition_delay", 1.5)))
            else:
                self.tap_text(self.frame(), step["text"], step["roi"])
            if step.get("confirm_screen") and not self.bot.confirm_screen(
                    must_screen=step["confirm_screen"], timeout=8, where="shield navigation"):
                raise ShieldUIError("Shield navigation screen was not confirmed")
        return self.frame()

    def inventory_view(self):
        frame = self.frame()
        if "buff info" not in self.text(frame, "inventory_title_roi").lower():
            frame = self.navigate()
        if "buff info" not in self.text(frame, "inventory_title_roi").lower():
            raise ShieldUIError("Buff Info inventory panel was not confirmed")
        if not self.is_shield_panel(frame):
            raise ShieldUIError("Buff Info panel is not Peace Shield")
        return frame

    def is_shield_panel(self, frame):
        if re.search(r"peace\s*shield", self.text(frame, "timer_roi"), re.I):
            return True
        templates=getattr(self.bot,'templates',{})
        if templates.get('shield_panel_identity') is None or not self.cfg.get('timer_roi'):
            return False
        return bool(context._template_match_centers(frame,
            templates.get("shield_panel_identity"), tuple(self.cfg["timer_roi"]),
            threshold=.92, max_matches=1))

    def row(self, frame, hours):
        roi = tuple(self.cfg["inventory_roi"])
        hits = context._template_match_centers(frame, self.bot.templates.get(f"shield_inventory_{hours}h"),
                                               roi, threshold=.88, max_matches=4)
        other_hours = 8 if hours == 24 else 24
        others = context._template_match_centers(frame, self.bot.templates.get(f"shield_inventory_{other_hours}h"),
                                                 roi, threshold=.88, max_matches=4)
        # The silhouettes are similar: the chosen duration must beat the
        # competing duration at that same position, not just resemble a shield.
        hits = [hit for hit in hits if not any(abs(hit[0]-other[0]) < 50 and abs(hit[1]-other[1]) < 50
                                               and other[2] >= hit[2] for other in others)]
        if len(hits) != 1:
            raise ShieldUIError("Exact shield-duration icon was missing or ambiguous")
        x, y = hits[0][:2]
        # Count and Use are scoped to this detected row, not a fixed list slot.
        count_roi = (x + 70, y + 5, min(690, x + 490), y + 105)
        count = owned_count(context._ocr_frame_text(frame, count_roi, psm=7))
        if count is None:
            raise ShieldUIError("Owned count for selected shield was unreadable")
        return count, (700, y - 80, 975, y + 100)

    def inventory(self, hours, frame=None):
        frame = self.inventory_view() if frame is None else frame
        count, _ = self.row(frame, hours)
        return frame, count, frame

    def use_target(self, frame, roi):
        # Full plain-Use button template, scoped to the verified duration row.
        # Never accept the different Purchase & Use control on the 3-day row.
        hits = context._template_match_centers(frame, self.bot.templates.get("shield_use_button"),
                                               tuple(roi), threshold=.95, max_matches=2)
        if len(hits) != 1:
            raise ShieldUIError("Plain Use button was missing or ambiguous")
        return hits[0][:2]

    def replacement_confirm_target(self, frame):
        """Require both the exact observed warning and its yellow Confirm control."""
        templates = getattr(self.bot, "templates", {})
        if templates.get("shield_replacement_prompt") is None or templates.get("shield_replacement_confirm") is None:
            return None
        roi = tuple(self.cfg["confirmation_roi"])
        warning = context._template_match_centers(frame, templates["shield_replacement_prompt"], roi,
                                                  threshold=.94, max_matches=2)
        button = context._template_match_centers(frame, templates["shield_replacement_confirm"], roi,
                                                 threshold=.94, max_matches=2)
        return button[0][:2] if len(warning) == 1 and len(button) == 1 else None

    def activate(self, hours, detail, replacing):
        current = self.inventory_view()
        expected_count, _ = self.row(detail, hours)
        count, use_roi = self.row(current, hours)
        if count != expected_count:
            raise ShieldUIError("Inventory changed since the before screenshot; no item used")
        if count < 1:
            raise ShieldUIError("No requested shield in inventory")
        self.bot.adb_tap(*self.use_target(current, use_roi))
        time.sleep(float(self.cfg.get("transition_delay", 1.5)))
        frame = self.frame()
        # Consuming the last item changes its background row to Purchase & Use.
        # A verified active countdown is not a confirmation dialog. The caller
        # still independently checks the inventory delta and a fresh timer.
        for attempt in range(3):
            if self.is_shield_panel(frame):
                remaining = self.panel_seconds(frame)
                expected = hours * 3600
                if remaining is not None and expected - int(self.cfg.get("timer_tolerance_seconds", 180)) <= remaining <= expected + 60:
                    return
            if self.replacement_confirm_target(frame) is not None:
                break
            if attempt < 2:
                time.sleep(0.5)
                frame = self.frame()
        self.bot._shield_failure_frame=frame
        prompt = self.text(frame, "confirmation_roi")
        confirm_point = self.replacement_confirm_target(frame)
        if confirm_point is not None and self.cfg.get("replacement_text_roi"):
            # Do not confuse dimmed inventory Purchase & Use rows behind this
            # positively identified modal with its own warning/authorization.
            prompt = context._ocr_frame_text(frame, tuple(self.cfg["replacement_text_roi"]), psm=6)
        forbidden = re.search(r"purchase|diamonds|not\s+enough", prompt, re.I)
        if not forbidden and (replacement_prompt(prompt, hours) or confirm_point is not None):
            if not replacing or not self.cfg.get("allow_replacement", False):
                self.bot.adb_keyevent(4)
                raise ShieldUIError("Shield replacement was not authorized")
            if confirm_point is not None:
                self.bot.adb_tap(*confirm_point)
                time.sleep(float(self.cfg.get("transition_delay", 1.5)))
            elif shield_hours(prompt) == hours:
                self.tap_text(frame, "Confirm", self.cfg["confirmation_roi"])
            else:
                self.bot.adb_keyevent(4)
                raise ShieldUIError("Replacement warning was read but its exact Confirm control was not verified")
        elif re.search(r"confirm|replace|purchase|diamonds", prompt, re.I):
            self.bot.adb_keyevent(4)
            raise ShieldUIError("Unknown confirmation was cancelled; manual review required")

    def panel_seconds(self, frame):
        text = self.text(frame, "timer_roi")
        identified = self.is_shield_panel(frame)
        if identified and self.cfg.get("countdown_roi"):
            precise = self.numeric_countdown(frame)
            if precise is not None:
                return precise
        if identified and not re.search(r"peace\s*shield", text, re.I):
            text = "Peace Shield " + text
        remaining = shield_seconds(text)
        if remaining is None and re.search(r"peace\s*shield", text, re.I) and re.search(r"\binactive\b|not active", text, re.I):
            return 0
        if remaining is None and identified and self.cfg.get("countdown_roi"):
            # The outlined header can confuse multiline OCR. Read just its
            # countdown bar, but only after independently identifying the panel.
            countdown = context._ocr_frame_text(frame, tuple(self.cfg["countdown_roi"]), psm=7)
            remaining = shield_seconds("Peace Shield " + countdown)
        return remaining

    def numeric_countdown(self, frame):
        """Require two agreeing OCR preparations of the outlined timer digits."""
        x1,y1,x2,y2 = self.cfg["countdown_roi"]
        crop = frame[y1:y2,x1:x2]
        if crop.size == 0:
            return None
        gray = cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
        white = cv2.inRange(cv2.cvtColor(crop,cv2.COLOR_BGR2HSV),(0,0,200),(180,65,255))
        readings = []
        for image in (gray,255-white):
            image = cv2.resize(image,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC)
            image = cv2.copyMakeBorder(image,15,15,15,15,cv2.BORDER_CONSTANT,value=255)
            try:
                text = pytesseract.image_to_string(image,config='--psm 7 -c tessedit_char_whitelist=0123456789:').strip()
            except Exception:
                return None
            readings.append(shield_seconds("Peace Shield " + text))
        return readings[0] if readings[0] is not None and readings[0] == readings[1] else None

    def timer(self):
        for attempt in range(3):
            frame = self.inventory_view()
            remaining = self.panel_seconds(frame)
            if remaining is not None:
                return frame, remaining
            if attempt < 2:
                time.sleep(0.5)
        raise ShieldUIError("Shield countdown was unreadable or ambiguous")
