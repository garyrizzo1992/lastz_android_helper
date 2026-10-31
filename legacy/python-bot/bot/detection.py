"""Detection services extracted from the application facade."""
import cv2
import numpy as np
import time
import os
from difflib import SequenceMatcher
import pytesseract
import re
from pathlib import Path
from bot.context import context


def _hex_to_hsv(hex_color: str) -> tuple[int, int, int]:
    """
    Convert a CSS hex colour string (e.g. "#52B842" or "52B842") to an OpenCV
    HSV triplet (H: 0-179, S: 0-255, V: 0-255) suitable for cv2.inRange().

    Falls back to a golden-yellow default ("EDC568") if the input is empty or
    not exactly 6 hex digits after stripping the leading '#'.

    Used to pre-compute the HSV centre for the truck-plus button colour blob
    detector at bot startup.
    """
    hex_color = (hex_color or "").lstrip("#")
    if len(hex_color) != 6:
        hex_color = "EDC568"
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    bgr = np.uint8([[[b, g, r]]])
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[0][0]
    return int(hsv[0]), int(hsv[1]), int(hsv[2])


def _parse_fraction(text: str | None) -> tuple[int, int] | None:
    """Parse UI counters such as ``4/4`` and ``0/1,000``."""
    match = re.search(r"(\d[\d,]*)\s*/\s*(\d[\d,]*)", text or "")
    if not match:
        return None
    used = int(match.group(1).replace(",", ""))
    total = int(match.group(2).replace(",", ""))
    if total <= 0 or used < 0 or used > total:
        return None
    return used, total


def _template_match_centers(
    screenshot: np.ndarray | None,
    template: np.ndarray | None,
    roi: tuple[int, int, int, int],
    *,
    threshold: float,
    max_matches: int = 8,
) -> list[tuple[int, int, float]]:
    """Return non-overlapping grayscale template matches as centre points."""
    if screenshot is None or template is None:
        return []
    x1, y1, x2, y2 = (int(value) for value in roi)
    crop = screenshot[y1:y2, x1:x2]
    if crop.size == 0:
        return []
    template_bgr = template[:, :, :3] if template.ndim == 3 else template
    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    template_gray = (
        cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
        if template_bgr.ndim == 3
        else template_bgr
    )
    height, width = template_gray.shape[:2]
    if crop_gray.shape[0] < height or crop_gray.shape[1] < width:
        return []

    scores = cv2.matchTemplate(crop_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    matches: list[tuple[int, int, float]] = []
    suppression_x = max(20, int(width * 0.8))
    suppression_y = max(20, int(height * 0.8))
    for _ in range(max(1, int(max_matches))):
        _, score, _, location = cv2.minMaxLoc(scores)
        if float(score) < float(threshold):
            break
        left, top = location
        matches.append((x1 + left + width // 2, y1 + top + height // 2, float(score)))
        cv2.rectangle(
            scores,
            (max(0, left - suppression_x), max(0, top - suppression_y)),
            (
                min(scores.shape[1] - 1, left + suppression_x),
                min(scores.shape[0] - 1, top + suppression_y),
            ),
            -1.0,
            thickness=-1,
        )
    return matches


def _ocr_troop_capacity(
    screenshot: np.ndarray | None,
    value_rois: list[tuple[int, int, int, int]] | tuple[tuple[int, int, int, int], ...],
) -> tuple[int, int] | None:
    """Read the selected/max Troop Capacity fraction from a march dialog."""
    if screenshot is None:
        return None
    for roi in value_rois:
        x1, y1, x2, y2 = (int(value) for value in roi)
        crop = screenshot[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        variants = (
            gray,
            cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
            cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1],
        )
        for image in variants:
            try:
                text = pytesseract.image_to_string(
                    image,
                    config="--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789/,",
                ).strip()
            except Exception:
                continue
            capacity = context._parse_fraction(text)
            if capacity is not None:
                return capacity
    return None


def _visible_troop_card_centers(screenshot, card_y, fallback):
    """Locate card outlines after scrolling instead of assuming old x positions."""
    if screenshot is None:
        return tuple(fallback)
    y1, y2 = card_y
    crop = screenshot[max(0, y1 - 45):min(screenshot.shape[0], y2 + 25)]
    edges = cv2.Canny(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), 40, 100)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    rectangles = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if 110 <= width <= 235 and 125 <= height <= 235:
            rectangles.append((width * height, x + width // 2))
    centers = []
    for _, center in sorted(rectangles, reverse=True):
        if all(abs(center - old) > 70 for old in centers):
            centers.append(center)
    return tuple(sorted(centers)) if len(centers) >= 2 else tuple(fallback)


def _is_lower_tier_training_warning(text):
    normalized = re.sub(r"[^a-z]", "", (text or "").lower())
    return "highertier" in normalized and "lowertier" in normalized


def _parse_shop_reset_seconds(text):
    """Read the shop's labelled countdown, never guess a weekday/timezone."""
    normalized = (text or "").lower()
    if not any(word in normalized for word in ("reset", "refresh")):
        return None
    match = re.search(r"(?:(\d+)\s*d\s*)?(\d{1,2})\s*:\s*(\d{2})\s*:\s*(\d{2})", normalized)
    if not match:
        return None
    days, hours, minutes, seconds = (int(value or 0) for value in match.groups())
    total = days * 86400 + hours * 3600 + minutes * 60 + seconds
    return total if hours < 24 and minutes < 60 and seconds < 60 and 0 < total <= 604800 else None


def _troop_tier_card_states(
    screenshot: np.ndarray | None,
    centers: tuple[int, ...] | list[int],
    *,
    card_y: tuple[int, int],
    half_width: int = 75,
    unlocked_ratio: float = 0.15,
    selected_ratio: float = 0.005,
) -> list[dict]:
    """Classify visible troop-tier cards as unlocked/locked and selected."""
    if screenshot is None:
        return []
    hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
    frame_height, frame_width = screenshot.shape[:2]
    y1, y2 = (int(value) for value in card_y)
    y1, y2 = max(0, y1), min(frame_height, y2)
    states = []
    for index, center_x in enumerate(centers):
        center_x = int(center_x)
        x1, x2 = max(0, center_x - half_width), min(frame_width, center_x + half_width)
        card = hsv[y1:y2, x1:x2]
        if card.size == 0:
            continue
        saturated = (card[:, :, 1] > 70) & (card[:, :, 2] > 50)
        unlocked_score = float(np.mean(saturated))

        select_x1 = max(0, center_x - half_width - 25)
        select_x2 = min(frame_width, center_x + half_width + 25)
        select_y1, select_y2 = max(0, y1 - 40), min(frame_height, y2 + 30)
        selection_area = hsv[select_y1:select_y2, select_x1:select_x2]
        yellow = (
            (selection_area[:, :, 0] >= 15)
            & (selection_area[:, :, 0] <= 40)
            & (selection_area[:, :, 1] > 120)
            & (selection_area[:, :, 2] > 150)
        )
        selected_score = float(np.mean(yellow))
        states.append(
            {
                "index": index,
                "center": (center_x, (y1 + y2) // 2),
                "unlocked": unlocked_score >= unlocked_ratio,
                "selected": selected_score >= selected_ratio,
                "unlocked_score": unlocked_score,
                "selected_score": selected_score,
            }
        )
    return states


def _highest_visible_unlocked_troop_card(states: list[dict]) -> dict | None:
    """Return the rightmost visible unlocked troop-tier card."""
    unlocked = [state for state in states if state.get("unlocked")]
    return max(unlocked, key=lambda state: state["index"]) if unlocked else None


def _parse_power_value(text: str | None) -> float | None:
    """Parse a displayed combat power such as ``3.51M`` or ``428.24M``."""
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*([KMB])", (text or "").upper())
    if not match:
        return None
    value = float(match.group(1).replace(",", "."))
    multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[match.group(2)]
    return value * multiplier


def _find_world_bounty_markers(
    screenshot: np.ndarray | None,
    config: dict | None = None,
) -> list[dict]:
    """Return likely coloured bounty-bag markers inside the safe map area.

    Bounty bags can be purple, blue, or orange.  Detection deliberately errs
    on the broad side because every tap is subsequently gated by OCR-confirming
    a visible ``Plunder`` action.  Requiring the dark level badge immediately
    below the coloured object removes most HUD and terrain false positives.
    """
    if screenshot is None or screenshot.ndim < 3:
        return []

    cfg = config or {}
    height, width = screenshot.shape[:2]
    raw_roi = cfg.get("scan_roi", (120, 340, 720, 1720))
    x1, y1, x2, y2 = (int(value) for value in raw_roi)
    x1 = max(0, min(x1, width - 1))
    y1 = max(0, min(y1, height - 1))
    x2 = max(x1 + 1, min(x2, width))
    y2 = max(y1 + 1, min(y2, height))
    roi = screenshot[y1:y2, x1:x2]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    color_ranges = cfg.get(
        "hsv_ranges",
        {
            "purple": ((120, 85, 65), (175, 255, 255)),
            "blue": ((88, 85, 65), (124, 255, 255)),
            "orange": ((3, 105, 80), (27, 255, 255)),
        },
    )
    min_area = float(cfg.get("min_color_area", 45))
    max_area = float(cfg.get("max_color_area", 12000))
    min_badge_ratio = float(cfg.get("min_dark_badge_ratio", 0.055))
    kernel = np.ones((3, 3), dtype=np.uint8)
    candidates: list[dict] = []

    for color_name, (lower, upper) in color_ranges.items():
        mask = cv2.inRange(
            hsv,
            np.array(lower, dtype=np.uint8),
            np.array(upper, dtype=np.uint8),
        )
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = float(cv2.contourArea(contour))
            if not min_area <= area <= max_area:
                continue
            x, y, marker_w, marker_h = cv2.boundingRect(contour)
            if not (8 <= marker_w <= 190 and 8 <= marker_h <= 180):
                continue
            aspect = marker_w / float(max(marker_h, 1))
            fill_ratio = area / float(max(marker_w * marker_h, 1))
            if not (0.30 <= aspect <= 3.2 and fill_ratio >= 0.14):
                continue

            badge_pad_x = max(5, marker_w // 3)
            badge_height = max(20, min(70, marker_h + 18))
            bx1 = max(0, x - badge_pad_x)
            bx2 = min(roi.shape[1], x + marker_w + badge_pad_x)
            by1 = min(roi.shape[0], y + marker_h)
            by2 = min(roi.shape[0], by1 + badge_height)
            if bx2 <= bx1 or by2 <= by1:
                continue
            badge_hsv = hsv[by1:by2, bx1:bx2]
            # Level badges are nearly black; keeping V strict prevents normal
            # olive/green terrain from satisfying the badge requirement.
            dark = cv2.inRange(badge_hsv, (0, 0, 0), (180, 210, 80))
            dark_ratio = float(np.count_nonzero(dark)) / float(dark.size)
            if dark_ratio < min_badge_ratio:
                continue

            candidates.append(
                {
                    "center": (x1 + x + marker_w // 2, y1 + y + marker_h // 2),
                    "bbox": (x1 + x, y1 + y, marker_w, marker_h),
                    "color": color_name,
                    "score": round(area * (1.0 + dark_ratio), 3),
                    "dark_badge_ratio": round(dark_ratio, 4),
                }
            )

    # Nearby colour components often belong to the same illustrated bag.
    # Keep the strongest one so a single object is not tapped repeatedly.
    deduped: list[dict] = []
    color_priority = {"purple": 3, "blue": 2, "orange": 1}
    for candidate in sorted(
        candidates,
        key=lambda item: (color_priority.get(item["color"], 0), item["score"]),
        reverse=True,
    ):
        cx, cy = candidate["center"]
        if any((cx - ox) ** 2 + (cy - oy) ** 2 < 55 ** 2 for ox, oy in (item["center"] for item in deduped)):
            continue
        deduped.append(candidate)
    return deduped


def _world_info_card_visible(screenshot: np.ndarray | None) -> bool:
    """Detect the large light resource/object card shown after a map tap."""
    if screenshot is None or screenshot.shape[0] < 1050 or screenshot.shape[1] < 700:
        return False
    card_roi = screenshot[500:1020, 0:680]
    hsv = cv2.cvtColor(card_roi, cv2.COLOR_BGR2HSV)
    light_neutral = cv2.inRange(hsv, (0, 0, 145), (180, 105, 255))
    ratio = float(np.count_nonzero(light_neutral)) / float(light_neutral.size)
    return ratio >= 0.18


def _world_coordinate_form_visible(screenshot: np.ndarray | None) -> bool:
    """Return True while the blue submit magnifier is present in the top form."""
    if screenshot is None or screenshot.shape[0] < 340 or screenshot.shape[1] < 900:
        return False
    button_roi = screenshot[225:340, 790:900]
    hsv = cv2.cvtColor(button_roi, cv2.COLOR_BGR2HSV)
    blue = cv2.inRange(hsv, (88, 80, 80), (125, 255, 255))
    ratio = float(np.count_nonzero(blue)) / float(blue.size)
    return ratio >= 0.10


def _alliance_help_point(frame, templates):
    """Match only the base HUD's ally-help shortcut, not research Help pins."""
    cfg = context.CONFIG.get("alliance_help", {})
    candidates = []
    for name in ("alliance_help_handshake", "help"):
        candidates.extend(context._template_match_centers(
            frame, templates.get(name), cfg.get("roi", (760, 1450, 980, 1750)),
            threshold=float(cfg.get("threshold", 0.88)), max_matches=1,
        ))
    return max(candidates, key=lambda hit: hit[2])[:2] if candidates else None


def _ocr_frame_text(
    screenshot: np.ndarray | None,
    roi: tuple[int, int, int, int] | None = None,
    psm: int = 11,
) -> str:
    """OCR a supplied frame/ROI without taking another device screenshot."""
    if screenshot is None:
        return ""
    height, width = screenshot.shape[:2]
    if roi is None:
        crop = screenshot
    else:
        x1, y1, x2, y2 = (int(value) for value in roi)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
        if x2 <= x1 or y2 <= y1:
            return ""
        crop = screenshot[y1:y2, x1:x2]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
    try:
        return pytesseract.image_to_string(gray, config=f"--oem 3 --psm {int(psm)}").strip()
    except Exception:
        return ""


def _parse_healing_duration_seconds(text: str | None) -> int | None:
    """Parse the Hospital Heal-button timer as seconds."""
    normalized = (text or "").upper().replace("O", "0")
    match = re.search(r"(\d{1,2})\s*:\s*(\d{2})\s*:\s*(\d{2})", normalized)
    if match:
        hours, minutes, seconds = (int(value) for value in match.groups())
        if minutes < 60 and seconds < 60:
            return hours * 3600 + minutes * 60 + seconds

    match = re.search(r"(?<!\d)(\d{1,3})\s*:\s*(\d{2})(?!\d)", normalized)
    if match:
        minutes, seconds = (int(value) for value in match.groups())
        if seconds < 60:
            return minutes * 60 + seconds
    return None


def _is_alliance_speedup_reward_dialog(screenshot: np.ndarray | None) -> bool:
    """Detect the variable-name/duration alliance speedup reward dialog."""
    if screenshot is None:
        return False
    panel = screenshot[400:1500, 120:960]
    if panel.size == 0:
        return False
    hsv = cv2.cvtColor(panel, cv2.COLOR_BGR2HSV)
    orange = cv2.inRange(hsv, (4, 100, 80), (22, 255, 255))
    if float(np.count_nonzero(orange)) / float(orange.size) < 0.45:
        return False
    text = context._ocr_frame_text(screenshot, (120, 600, 960, 1450), psm=11)
    normalized = re.sub(r"[^a-z]+", " ", text.lower())
    return all(word in normalized.split() for word in ("speedup", "duration", "confirm"))


def _base_recovery_evidence(
    detected: dict | None,
    *,
    home_marker_visible: bool,
    home_marker_seen_at: float | None,
    now: float,
    min_sanity_matches: int = 2,
    marker_grace_seconds: float = 8.0,
) -> dict:
    """Combine stable HUD and optional animated-marker evidence for navigation.

    The animated Home marker is useful extra evidence but is not persistent.
    A stable, two-region Home HUD is sufficient on its own; otherwise a base
    that is visibly home can be rejected forever after the marker animation
    disappears.
    """
    detected = detected or {}
    home_check = next(
        (
            check
            for check in detected.get("checks", [])
            if check.get("screen") == "home"
        ),
        {},
    )
    marker_recent = bool(
        home_marker_visible
        or (
            home_marker_seen_at is not None
            and now - float(home_marker_seen_at) <= float(marker_grace_seconds)
        )
    )
    strong_home = bool(
        home_check.get("ok")
        and int(home_check.get("matches", 0)) >= int(min_sanity_matches)
    )
    ordinary_home = bool(home_check.get("ok"))
    return {
        "candidate": bool(
            strong_home
            or (home_marker_visible and ordinary_home)
        ),
        "strong_home": strong_home,
        "marker_recent": marker_recent,
        "matches": int(home_check.get("matches", 0)),
        "score": float(home_check.get("score", -1.0)),
    }


def _ocr_healing_duration_seconds(
    screenshot: np.ndarray | None,
    roi: tuple[int, int, int, int],
) -> int | None:
    """Read the effective duration printed inside the blue Heal button."""
    if screenshot is None:
        return None
    x1, y1, x2, y2 = roi
    crop = screenshot[y1:y2, x1:x2]
    if crop.size == 0:
        return None
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
    variants = (
        gray,
        cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)[1],
        cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY_INV)[1],
    )
    for image in variants:
        for psm in (6, 7, 11):
            try:
                text = pytesseract.image_to_string(
                    image,
                    config=f"--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789:",
                )
            except Exception:
                continue
            duration = context._parse_healing_duration_seconds(text)
            if duration is not None:
                return duration
    return None


def _next_healing_slider_position(
    current_x: int,
    duration: int,
    target: int,
    min_x: int,
    max_x: int,
    lower_sample: tuple[int, int] | None = None,
    upper_sample: tuple[int, int] | None = None,
) -> tuple[int, tuple[int, int] | None, tuple[int, int] | None]:
    """Choose the next slider position, interpolating once target is bracketed."""
    sample = (int(current_x), int(duration))
    if duration < target:
        lower_sample = sample
    elif duration > target:
        upper_sample = sample

    if lower_sample is not None and upper_sample is not None:
        lower_x, lower_duration = lower_sample
        upper_x, upper_duration = upper_sample
        if lower_x < upper_x and lower_duration < target < upper_duration:
            fraction = (target - lower_duration) / float(upper_duration - lower_duration)
            proposed = int(round(lower_x + fraction * (upper_x - lower_x)))
            next_x = max(lower_x + 1, min(upper_x - 1, proposed))
            return next_x, lower_sample, upper_sample

    # Establish the missing side of the bracket conservatively. Near the live
    # target the slider changes by roughly 30 seconds per pixel.
    step = max(4, min(45, int(round(abs(target - duration) / 30.0))))
    if duration < target:
        next_x = min(max_x, current_x + step)
    else:
        next_x = max(min_x + 4, current_x - step)
    return next_x, lower_sample, upper_sample


def _find_masked_template_in_roi(
    screenshot: np.ndarray | None,
    template: np.ndarray | None,
    roi: tuple[int, int, int, int],
    max_score: float,
) -> tuple[int, int, float] | None:
    """Return an alpha-aware SQDIFF match scoped to an absolute screen ROI."""
    if screenshot is None or template is None:
        return None
    height, width = screenshot.shape[:2]
    x1, y1, x2, y2 = (int(value) for value in roi)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(width, x2), min(height, y2)
    if x2 <= x1 or y2 <= y1:
        return None
    crop = screenshot[y1:y2, x1:x2]
    template_bgr = template[:, :, :3] if template.ndim == 3 else template
    if crop.shape[0] < template_bgr.shape[0] or crop.shape[1] < template_bgr.shape[1]:
        return None
    mask = None
    if template.ndim == 3 and template.shape[2] == 4:
        mask = template[:, :, 3]
    result = cv2.matchTemplate(crop, template_bgr, cv2.TM_SQDIFF_NORMED, mask=mask)
    finite = np.isfinite(result)
    if not np.any(finite):
        return None
    safe_result = np.where(finite, result, np.inf)
    min_index = np.unravel_index(int(np.argmin(safe_result)), safe_result.shape)
    score = float(safe_result[min_index])
    if score > float(max_score):
        return None
    return x1 + int(min_index[1]), y1 + int(min_index[0]), score


def _locate_available_builder_button(
    screenshot: np.ndarray | None,
    template: np.ndarray | None,
    roi: tuple[int, int, int, int] = (600, 650, 950, 1600),
    max_score: float = 0.02,
) -> tuple[int, int, float] | None:
    """Locate the first green Build button in the available Builder rows.

    The first Builder row can be occupied and show a blue ``Speed Up`` button.
    A free worker may also be the first row, especially on accounts with just
    one unlocked builder. Search every row; the exact green Build template
    provides the safety check, rather than excluding the first row spatially.
    """
    match = context._find_masked_template_in_roi(screenshot, template, roi, max_score)
    if match is None or template is None:
        return None
    left, top, score = match
    template_height, template_width = template.shape[:2]
    return (
        left + template_width // 2,
        top + min(95, template_height - 5),
        score,
    )


def _locate_boomer_event_card(
    screenshot: np.ndarray | None,
    template: np.ndarray | None,
    roi: tuple[int, int, int, int] = (0, 1850, 1080, 2160),
    scale: float = 0.75,
    min_score: float = 0.82,
) -> tuple[int, int, float] | None:
    """Locate Boomer's portrait in the Event Center carousel.

    The live card title uses a decorative font that Tesseract commonly reads
    as ``Danger murice`` or only ``...jer lurks``.  The portrait itself is
    stable, so it is the reliable fallback for selecting Danger Lurks.
    """
    if screenshot is None or template is None:
        return None
    height, width = screenshot.shape[:2]
    x1, y1, x2, y2 = (int(value) for value in roi)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(width, x2), min(height, y2)
    if x2 <= x1 or y2 <= y1:
        return None

    crop = screenshot[y1:y2, x1:x2]
    template_bgr = template[:, :, :3] if template.ndim == 3 else template
    scaled_width = max(5, int(round(template_bgr.shape[1] * float(scale))))
    scaled_height = max(5, int(round(template_bgr.shape[0] * float(scale))))
    if crop.shape[0] < scaled_height or crop.shape[1] < scaled_width:
        return None
    scaled = cv2.resize(
        template_bgr,
        (scaled_width, scaled_height),
        interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC,
    )
    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(crop_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    _, score, _, location = cv2.minMaxLoc(result)
    if float(score) < float(min_score):
        return None
    return (
        x1 + location[0] + scaled_width // 2,
        y1 + location[1] + scaled_height // 2,
        float(score),
    )


def _hospital_row_availability(
    screenshot: np.ndarray | None,
    header_y_positions: list[int] | tuple[int, ...],
) -> list[int]:
    """OCR the available injured count for each visible Hospital row."""
    counts = [0 for _ in header_y_positions]
    if screenshot is None:
        return counts
    crop_y1, crop_y2 = 600, min(1450, screenshot.shape[0])
    crop_x1, crop_x2 = 250, min(700, screenshot.shape[1])
    crop = screenshot[crop_y1:crop_y2, crop_x1:crop_x2]
    try:
        data = pytesseract.image_to_data(
            crop,
            config="--oem 3 --psm 6",
            output_type=pytesseract.Output.DICT,
        )
    except Exception:
        return counts

    for index, raw_text in enumerate(data.get("text", [])):
        token = re.sub(r"\D", "", raw_text or "")
        if not token:
            continue
        left = crop_x1 + int(data["left"][index])
        top = crop_y1 + int(data["top"][index])
        if not (350 <= left <= 650):
            continue
        nearest = min(range(len(header_y_positions)), key=lambda i: abs(top - header_y_positions[i]))
        if abs(top - header_y_positions[nearest]) > 45:
            continue
        counts[nearest] = max(counts[nearest], int(token))
    return counts


def _find_ocr_word_center(
    screenshot: np.ndarray | None,
    needle: str,
    roi: tuple[int, int, int, int] | None = None,
) -> tuple[int, int] | None:
    """Locate a word with Tesseract and return its centre in screen pixels."""
    if screenshot is None:
        return None
    height, width = screenshot.shape[:2]
    if roi is None:
        x1, y1, x2, y2 = 0, 0, width, height
    else:
        x1, y1, x2, y2 = (int(value) for value in roi)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
    if x2 <= x1 or y2 <= y1:
        return None
    crop = screenshot[y1:y2, x1:x2]
    scale = 2.0
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    enlarged = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    wanted = re.sub(r"[^a-z]", "", needle.lower())
    for psm in (11, 6):
        try:
            data = pytesseract.image_to_data(
                enlarged, config=f"--oem 3 --psm {psm}",
                output_type=pytesseract.Output.DICT,
            )
        except Exception:
            continue
        for index, raw_text in enumerate(data.get("text", [])):
            word = re.sub(r"[^a-z]", "", (raw_text or "").lower())
            if not word or not (word == wanted or word.startswith(wanted[:5])):
                continue
            left = int(data["left"][index]) / scale
            top = int(data["top"][index]) / scale
            word_w = int(data["width"][index]) / scale
            word_h = int(data["height"][index]) / scale
            return int(x1 + left + word_w / 2), int(y1 + top + word_h / 2)
    return None


def _find_ocr_phrase_center(
    screenshot: np.ndarray | None,
    phrase: str,
    roi: tuple[int, int, int, int] | None = None,
) -> tuple[int, int] | None:
    """Locate a short adjacent OCR phrase and return its screen centre."""
    if screenshot is None:
        return None
    height, width = screenshot.shape[:2]
    if roi is None:
        x1, y1, x2, y2 = 0, 0, width, height
    else:
        x1, y1, x2, y2 = (int(value) for value in roi)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
    if x2 <= x1 or y2 <= y1:
        return None

    wanted = re.sub(r"[^a-z0-9]", "", phrase.lower())
    if not wanted:
        return None
    crop = screenshot[y1:y2, x1:x2]
    scale = 2.0
    enlarged = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    try:
        data = pytesseract.image_to_data(
            enlarged,
            config="--oem 3 --psm 11",
            output_type=pytesseract.Output.DICT,
        )
    except Exception:
        return None

    words = []
    for index, raw_text in enumerate(data.get("text", [])):
        token = re.sub(r"[^a-z0-9]", "", (raw_text or "").lower())
        if not token:
            continue
        left = int(data["left"][index]) / scale
        top = int(data["top"][index]) / scale
        word_w = int(data["width"][index]) / scale
        word_h = int(data["height"][index]) / scale
        words.append({
            "token": token,
            "left": left,
            "top": top,
            "right": left + word_w,
            "bottom": top + word_h,
        })

    for start in range(len(words)):
        combined = ""
        group = []
        previous = None
        for current in words[start:start + 4]:
            if previous is not None:
                vertical_gap = abs(
                    (current["top"] + current["bottom"]) / 2
                    - (previous["top"] + previous["bottom"]) / 2
                )
                horizontal_gap = current["left"] - previous["right"]
                if vertical_gap > max(35, (current["bottom"] - current["top"]) * 1.5):
                    break
                if horizontal_gap > 220:
                    break
            combined += current["token"]
            group.append(current)
            if combined == wanted:
                left = min(item["left"] for item in group)
                top = min(item["top"] for item in group)
                right = max(item["right"] for item in group)
                bottom = max(item["bottom"] for item in group)
                return int(x1 + (left + right) / 2), int(y1 + (top + bottom) / 2)
            if not wanted.startswith(combined):
                break
            previous = current
    return None


def _is_unit_cap_message(text: str | None) -> bool:
    """Return True only for the Military Center's unit-cap warning."""
    normalized = re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()
    return "unit cap reached" in normalized and "military center" in normalized


def _is_construction_resource_shortage_prompt(text: str | None) -> bool:
    """Recognise Builder resource-shortage UI, including its Get More screen.

    This deliberately requires both the resource-shortage wording and one of
    the actions.  It prevents a generic inventory or resource screen from
    consuming items merely because it happens to contain the word
    ``Replenish``.
    """
    normalized = re.sub(r"[^a-z]+", " ", (text or "").lower()).strip()
    has_shortage = (
        "insufficient resource" in normalized
        or "not enough resource" in normalized
        or "lack of resource" in normalized
        or ("resource" in normalized and "insufficient" in normalized)
    )
    compact = normalized.replace(" ", "")
    has_get_more_replenish = "getmore" in compact and "replenishall" in compact
    return has_get_more_replenish or (
        has_shortage and ("replenish" in normalized or "skip" in normalized)
    )


def _is_construction_replenish_confirmation(text: str | None) -> bool:
    """Recognise the confirmation listing inventory packs to be consumed."""
    normalized = re.sub(r"[^a-z]+", " ", (text or "").lower()).strip()
    return (
        "replenish all" in normalized
        and "following resources will be used" in normalized
        and "confirm" in normalized
    )


def _is_boomer_auto_join_enabled(text: str | None) -> bool:
    """Return True only when the Danger Lurks dialog shows an active timer."""
    normalized = re.sub(r"[^a-z]+", " ", (text or "").lower()).strip()
    return "auto join duration" in normalized and "disabled" not in normalized


def _locate_green_builder_upgrade(frame: np.ndarray | None) -> tuple[int, int] | None:
    """Locate the green circular Upgrade action without depending on building text."""
    if frame is None or frame.shape[0] < 1500 or frame.shape[1] < 900:
        return None

    x1, y1, x2, y2 = (250, 950, 850, 1500)
    roi = frame[y1:y2, x1:x2]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, (35, 80, 80), (95, 255, 255))
    count, _, stats, _ = cv2.connectedComponentsWithStats(green)
    candidates = []

    for index in range(1, count):
        x, y, width, height, area = (int(value) for value in stats[index])
        if not (60 <= width <= 160 and 60 <= height <= 160 and area >= 1800):
            continue
        if not (0.65 <= width / float(height) <= 1.5):
            continue

        # The Upgrade action contains a large white upward arrow. This rejects
        # green resource pins and building arrows that share the same hue.
        patch_hsv = hsv[y:y + height, x:x + width]
        white = cv2.inRange(patch_hsv, (0, 0, 185), (180, 90, 255))
        white_count, _, white_stats, _ = cv2.connectedComponentsWithStats(white)
        arrow_parts = []
        for white_index in range(1, white_count):
            _, _, arrow_width, arrow_height, arrow_area = (
                int(value) for value in white_stats[white_index]
            )
            if (
                45 <= arrow_width <= 75
                and 50 <= arrow_height <= 85
                and arrow_area >= 1200
            ):
                arrow_parts.append(arrow_area)
        if not arrow_parts:
            continue

        center = (x1 + x + width // 2, y1 + y + height // 2)
        candidates.append((max(arrow_parts), area, center))

    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


def _locate_builder_help_pin(frame: np.ndarray | None) -> tuple[int, int] | None:
    """Locate the construction handshake pin in the recentered-building area."""
    if frame is None or frame.shape[0] < 900 or frame.shape[1] < 650:
        return None

    x1, y1, x2, y2 = (430, 730, 620, 900)
    roi = frame[y1:y2, x1:x2]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    pin_mask = cv2.inRange(hsv, (0, 0, 150), (180, 70, 255))
    count, _, stats, centroids = cv2.connectedComponentsWithStats(pin_mask)
    candidates = []

    for index in range(1, count):
        _, _, width, height, area = (int(value) for value in stats[index])
        if not (70 <= width <= 160 and 70 <= height <= 150 and area >= 2500):
            continue
        center_x, center_y = centroids[index]
        candidates.append((area, (x1 + int(round(center_x)), y1 + int(round(center_y)))))

    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _locate_green_rect_buttons(
    frame: np.ndarray | None,
    roi: tuple[int, int, int, int],
    *,
    min_width: int,
    max_width: int,
    min_height: int = 45,
    max_height: int = 140,
    hsv_lower: tuple[int, int, int] = (35, 70, 70),
    hsv_upper: tuple[int, int, int] = (95, 255, 255),
) -> list[tuple[int, int]]:
    """Return coloured rectangular button centres within a tightly scoped ROI."""
    if frame is None:
        return []

    frame_height, frame_width = frame.shape[:2]
    x1, y1, x2, y2 = roi
    x1, x2 = max(0, x1), min(frame_width, x2)
    y1, y2 = max(0, y1), min(frame_height, y2)
    if x2 <= x1 or y2 <= y1:
        return []

    cropped = frame[y1:y2, x1:x2]
    hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
    color_mask = cv2.inRange(hsv, hsv_lower, hsv_upper)
    count, _, stats, centroids = cv2.connectedComponentsWithStats(color_mask)
    buttons = []

    for index in range(1, count):
        _, _, width, height, area = (int(value) for value in stats[index])
        if not (
            min_width <= width <= max_width
            and min_height <= height <= max_height
            and area >= width * height * 0.45
        ):
            continue
        center_x, center_y = centroids[index]
        buttons.append((x1 + int(round(center_x)), y1 + int(round(center_y))))

    return sorted(buttons, key=lambda point: (point[1], point[0]))


def _alliance_shop_price_button(frame, artwork_center):
    """Find the gold price footer beneath matched art, never tap the tooltip.

    Scope detection to the same grid column and the bottom of that card.
    Clip the card borders: their gold pixels otherwise join adjacent rows.
    A clipped footer or a grey sold-out footer must fail closed.
    """
    x, y = artwork_center
    left, right = (75, 510) if x < frame.shape[1] / 2 else (570, 990)
    buttons = context._locate_green_rect_buttons(
        frame, (left, y + 110, right, min(y + 320, 1960)),
        min_width=330, max_width=450, min_height=55, max_height=140,
        hsv_lower=(5, 100, 100), hsv_upper=(40, 255, 255),
    )
    return min(buttons, key=lambda point: point[1]) if buttons else None


def _locate_boomer_activate_button(
    frame: np.ndarray | None,
    roi: tuple[int, int, int, int] = (500, 1500, 1000, 1800),
) -> tuple[int, int] | None:
    """Locate the large yellow/orange Activate button in the Boomer dialog."""
    if frame is None:
        return None

    frame_height, frame_width = frame.shape[:2]
    x1, y1, x2, y2 = roi
    x1, x2 = max(0, x1), min(frame_width, x2)
    y1, y2 = max(0, y1), min(frame_height, y2)
    if x2 <= x1 or y2 <= y1:
        return None

    cropped = frame[y1:y2, x1:x2]
    hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
    warm = cv2.inRange(hsv, (5, 100, 100), (40, 255, 255))
    count, _, stats, centroids = cv2.connectedComponentsWithStats(warm)
    candidates = []
    for index in range(1, count):
        _, _, width, height, area = (int(value) for value in stats[index])
        if not (
            300 <= width <= 480
            and 80 <= height <= 160
            and area >= width * height * 0.55
        ):
            continue
        center_x, center_y = centroids[index]
        candidates.append(
            (area, (x1 + int(round(center_x)), y1 + int(round(center_y))))
        )

    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _ocr_title_matches(actual: str | None, expected: str) -> bool:
    """Tolerate small OCR errors while still requiring the expected page name."""
    actual_normalized = re.sub(r"[^a-z]", "", (actual or "").lower())
    expected_normalized = re.sub(r"[^a-z]", "", expected.lower())
    if expected_normalized in actual_normalized:
        return True

    expected_tokens = re.findall(r"[a-z]+", expected.lower())
    non_alliance_tokens = [token for token in expected_tokens if token != "alliance"]
    # Tesseract has repeatedly read the large outlined title "Alliance" as
    # "Allianee5" (missing the c, with a trailing glyph). Match that token
    # fuzzily, but still require page-specific tokens such as gifts or techs.
    alliance_prefix = actual_normalized[: min(len(actual_normalized), 10)]
    alliance_match = (
        "liance" in actual_normalized
        or SequenceMatcher(None, alliance_prefix, "alliance").ratio() >= 0.72
    )
    return (
        alliance_match
        and all(token in actual_normalized for token in non_alliance_tokens)
    )


def _parse_attempts_fraction(text: str | None) -> tuple[int, int] | None:
    """Parse Attempts Left OCR, repairing merged leading digits such as 116/20."""
    counter = context._parse_fraction(text)
    if counter is not None:
        return counter

    match = re.search(r"(\d+)\s*/\s*(\d+)", (text or "").replace(",", ""))
    if not match:
        return None
    left_text, total_text = match.groups()
    total = int(total_text)
    while len(left_text) > 1 and int(left_text) > total:
        left_text = left_text[1:]
    left = int(left_text)
    if 0 <= left <= total <= 100:
        return left, total
    return None


def find_template(self, template_name, screenshot, threshold=0.05, click=False):
        """
        Locate a template image inside a screenshot using two complementary
        OpenCV methods.  Returns the top-left match coordinate on success, or
        None if no match is found.

        Matching pipeline
        -----------------
        All template images are loaded at startup into self.templates and
        referenced by string name (matching keys in CONFIG["image_paths"]).

        Step 1 — SQDIFF (cv2.TM_SQDIFF_NORMED)
            Runs first for most templates (see force_sqdiff_templates config).
            Score range 0.0 (perfect) – 1.0 (no match).  A match is accepted
            when score ≤ eff_threshold (default 0.05; overridable per-template
            via CONFIG["template_thresholds"]).
            Supports alpha-channel mask for transparent-background PNGs.

        Step 2 — CCOEFF grayscale (cv2.TM_CCOEFF_NORMED)
            Runs as primary path when CONFIG["grayscale_only"] is True, or as
            fallback when SQDIFF finds nothing.
            Score range -1.0 – 1.0.  Accepted when score ≥
            CONFIG["template_coeff_threshold"] (default 0.85).

        Scale loop
            Both methods iterate over a list of scale factors (fast mode:
            [1.0]; full mode: [1.0, 0.97, 1.03, 0.94, 1.06]) to tolerate
            slight resolution mismatches.  Per-template scale lists can
            override the global list via CONFIG["template_scales_per_template"].
            Scaled template crops are LRU-cached (max 200 entries) to avoid
            re-computing them on every call.

        Downscale optimisation
            When CONFIG["enable_matching_downscale"] is True, the screenshot is
            resized by CONFIG["matching_downscale"] (e.g. 0.6) before matching
            to reduce CPU time on slow hosts (Raspberry Pi).  Match coordinates
            are scaled back to original resolution before returning.

        Parameters
        ----------
        template_name : str
            Key into self.templates (and CONFIG["image_paths"]).
        screenshot : numpy.ndarray
            Full BGR frame to search within.
        threshold : float, optional
            SQDIFF acceptance threshold (ignored if a per-template override
            exists in CONFIG["template_thresholds"]).
        click : bool, optional
            If True, tap the match centre with adb_tap() on success and sleep
            action_delay seconds.

        Returns
        -------
        tuple[int, int] or None
            (x, y) top-left corner of the best match, or None.
        """
        self._perf_metrics['template_matches'] += 1
        template = self.templates.get(template_name)
        if template is None or screenshot is None:
            self.image_logger.warning(f"Template '{template_name}' not found or screenshot is None")
            return None

        # Apply per-template threshold if available
        thr_map = context.CONFIG.get("template_thresholds", {})
        eff_threshold = thr_map.get(template_name, threshold if threshold is not None else 0.05)

        # Prepare base images
        tpl_bgr = template[:, :, :3] if (len(template.shape) == 3 and template.shape[2] >= 3) else template
        scr_bgr = screenshot[:, :, :3] if (len(screenshot.shape) == 3 and screenshot.shape[2] >= 3) else screenshot

        # --- NEW: toggleable downscale ---
        g = float(
            context.CONFIG.get("matching_downscale", 1.0)
            if context.CONFIG.get("enable_matching_downscale", True)
            else 1.0
        )
        if g != 1.0:
            scr_work = cv2.resize(scr_bgr, (max(1, int(scr_bgr.shape[1]*g)), max(1, int(scr_bgr.shape[0]*g))), interpolation=cv2.INTER_AREA)
        else:
            scr_work = scr_bgr

        # Helper: cached resized template variants
        def _get_tpl_scaled(name: str, img: np.ndarray, scale: float, kind: str, mask: np.ndarray | None = None):
            key = (name, kind, int(round(scale*1000)))
            if key in self._tpl_cache:
                return self._tpl_cache[key]
            w = max(5, int(img.shape[1] * scale))
            h = max(5, int(img.shape[0] * scale))
            if kind == "mask":
                rs = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST) if mask is not None else None
            else:
                rs = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR)
            self._add_to_tpl_cache(key, rs)  # CHANGED: Use new method
            return rs

        grayscale_only = bool(context.CONFIG.get("grayscale_only", False))

        # Extract mask if present (only used by SQDIFF path)
        mask = None
        if len(template.shape) == 3 and template.shape[2] == 4 and np.any(template[:, :, 3] < 255):
            mask = template[:, :, 3]

        # Decide whether to run SQDIFF:
        force_tpl = template_name in context.CONFIG.get("force_sqdiff_templates", [])
        run_sqdiff = (not grayscale_only) or force_tpl or (mask is not None and np.any(mask < 255)) or context.CONFIG.get("force_sqdiff", False)

        # Choose scales according to fast/full mode with optional cap
        tpl_override_scales = context.CONFIG.get("template_scales_per_template", {}).get(template_name)
        if tpl_override_scales:
            scales = tpl_override_scales
        elif context.CONFIG.get("use_fast_scales", False):
            scales = context.CONFIG.get("template_scales_fast", [1.0])
        else:
            scales = context.CONFIG.get("template_scales", [1.0])
        max_attempts = int(context.CONFIG.get("max_scale_attempts", 0) or 0)
        if max_attempts > 0 and len(scales) > max_attempts:
            scales = scales[:max_attempts]

        best_match = None
        best_cc = None
        matched = False

        # Fast path: optionally skip SQDIFF to save CPU on Pi
        if run_sqdiff:
            for s in scales:
                s_eff = s * g
                tpl_rs = _get_tpl_scaled(template_name, tpl_bgr, s_eff, "bgr")
                mask_rs = _get_tpl_scaled(template_name, tpl_bgr, s_eff, "mask", mask=mask) if mask is not None else None
                if scr_work.shape[0] < tpl_rs.shape[0] or scr_work.shape[1] < tpl_rs.shape[1]:
                    continue
                res = cv2.matchTemplate(scr_work, tpl_rs, cv2.TM_SQDIFF_NORMED, mask=mask_rs)
                min_val, _, min_loc, _ = cv2.minMaxLoc(res)
                self.image_logger.trace(f"[SQDIFF] {template_name} scale={s:.2f} (eff={s_eff:.2f}) score={min_val:.4f} thr={eff_threshold}")
                if min_val <= eff_threshold:
                    w, h = tpl_rs.shape[1], tpl_rs.shape[0]
                    cx_ds = min_loc[0] + w // 2
                    cy_ds = min_loc[1] + h // 2
                    cx = int(round(cx_ds / g)) if g != 1.0 else cx_ds
                    cy = int(round(cy_ds / g)) if g != 1.0 else cy_ds
                    if click:
                        self.adb_tap(cx, cy)
                        self.game_logger.info(f"Clicked '{template_name}' (SQDIFF) at ({cx}, {cy})")
                        time.sleep(context.CONFIG["timing"]["action_delay"])
                    matched = True
                    self.image_logger.debug(f"Found '{template_name}' via SQDIFF at ({min_loc[0]}, {min_loc[1]})")
                    return (int(round(min_loc[0] / g)) if g != 1.0 else min_loc[0],
                            int(round(min_loc[1] / g)) if g != 1.0 else min_loc[1])
                if best_match is None or min_val < best_match[1]:
                    best_match = ("SQDIFF", min_val, min_loc, tpl_rs.shape[1], tpl_rs.shape[0])

        # Fallback/primary: Grayscale CCOEFF (faster)
        coeff_thr = context.CONFIG.get("template_coeff_threshold", 0.9)
        scr_gray_work = cv2.cvtColor(scr_work, cv2.COLOR_BGR2GRAY)
        tpl_gray_base = cv2.cvtColor(tpl_bgr, cv2.COLOR_BGR2GRAY) if len(tpl_bgr.shape) == 3 else tpl_bgr

        for s in scales:
            s_eff = s * g
            tpl_gray = _get_tpl_scaled(template_name, tpl_gray_base, s_eff, "gray")
            if scr_gray_work.shape[0] < tpl_gray.shape[0] or scr_gray_work.shape[1] < tpl_gray.shape[1]:
                continue
            res = cv2.matchTemplate(scr_gray_work, tpl_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            self.image_logger.trace(f"[CCOEFF] {template_name} scale={s:.2f} (eff={s_eff:.2f}) score={max_val:.4f} thr={coeff_thr}")
            if best_cc is None or max_val > best_cc[0]:
                best_cc = (max_val, max_loc, tpl_gray.shape[1], tpl_gray.shape[0])
            if max_val >= coeff_thr:
                w, h = tpl_gray.shape[1], tpl_gray.shape[0]
                cx_ds = max_loc[0] + w // 2
                cy_ds = max_loc[1] + h // 2
                cx = int(round(cx_ds / g)) if g != 1.0 else cx_ds
                cy = int(round(cy_ds / g)) if g != 1.0 else cy_ds
                if click:
                    self.adb_tap(cx, cy)
                    self.game_logger.info(f"Clicked '{template_name}' (CCOEFF) at ({cx}, {cy})")
                    time.sleep(context.CONFIG["timing"]["action_delay"])
                matched = True
                self.image_logger.debug(f"Found '{template_name}' via CCOEFF at ({max_loc[0]}, {max_loc[1]})")
                return (int(round(max_loc[0] / g)) if g != 1.0 else max_loc[0],
                        int(round(max_loc[1] / g)) if g != 1.0 else max_loc[1])

        # Fallback: if grayscale-only mode was enabled and CCOEFF failed, try SQDIFF anyway
        if grayscale_only:
            for s in scales:
                s_eff = s * g
                tpl_rs = cv2.resize(tpl_bgr, (max(5, int(tpl_bgr.shape[1]*s_eff)),
                                              max(5, int(tpl_bgr.shape[0]*s_eff))),
                                    interpolation=cv2.INTER_AREA if s_eff < 1.0 else cv2.INTER_LINEAR)
                mask_rs = None
                if mask is not None:
                    mask_rs = cv2.resize(mask, (tpl_rs.shape[1], tpl_rs.shape[0]), interpolation=cv2.INTER_NEAREST)
                if scr_work.shape[0] < tpl_rs.shape[0] or scr_work.shape[1] < tpl_rs.shape[1]:
                    continue
                res = cv2.matchTemplate(scr_work, tpl_rs, cv2.TM_SQDIFF_NORMED, mask=mask_rs)
                min_val, _, min_loc, _ = cv2.minMaxLoc(res)
                self.image_logger.trace(f"[FALLBACK SQDIFF] {template_name} scale={s:.2f} (eff={s_eff:.2f}) score={min_val:.4f} thr={eff_threshold}")
                if min_val <= eff_threshold:
                    w, h = tpl_rs.shape[1], tpl_rs.shape[0]
                    cx_ds = min_loc[0] + w // 2
                    cy_ds = min_loc[1] + h // 2
                    cx = int(round(cx_ds / g)) if g != 1.0 else cx_ds
                    cy = int(round(cy_ds / g)) if g != 1.0 else cy_ds
                    if click:
                        self.adb_tap(cx, cy)
                        self.game_logger.info(f"Clicked '{template_name}' (FALLBACK SQDIFF) at ({cx}, {cy})")
                        time.sleep(context.CONFIG["timing"]["action_delay"])
                    matched = True
                    self.image_logger.debug(f"Found '{template_name}' via FALLBACK SQDIFF at ({min_loc[0]}, {min_loc[1]})")
                    return (int(round(min_loc[0] / g)) if g != 1.0 else min_loc[0],
                            int(round(min_loc[1] / g)) if g != 1.0 else min_loc[1])

        # No accept; log best observed score to aid tuning
        if best_match:
            self.image_logger.debug(f"No match for '{template_name}'. Best SQDIFF={best_match[1]:.4f} at {best_match[2]}")
        if best_cc:
            self.image_logger.debug(f"No CCOEFF match for '{template_name}'. Best CCOEFF={best_cc[0]:.4f} at {best_cc[1]}")
        self._template_debug[template_name] = {
            "matched": matched,
            "sqdiff": best_match[1] if best_match else None,
            "ccoef": best_cc[0] if best_cc else None,
        }
        self.image_logger.trace(f"Template '{template_name}' not found after all attempts")
        return None


def wait_for_template(self, template_name, timeout=3.0, threshold=0.05, click=False):
        """
        Poll the screen until a template becomes visible or the timeout expires.

        Takes a new screenshot every 0.2 seconds and calls find_template().
        Returns the match location as soon as one is found, or None if the
        timeout is reached without a match.

        Parameters
        ----------
        template_name : str
            Key into self.templates.
        timeout : float
            Maximum seconds to wait before giving up.
        threshold : float
            SQDIFF acceptance threshold passed to find_template().
        click : bool
            If True, the matched location is tapped on the first successful
            match before returning.

        Returns
        -------
        tuple[int, int] or None
        """
        end = time.time() + timeout
        tries = 0
        while time.time() < end:
            tries += 1
            img = self.adb_screenshot()
            if img is None:
                time.sleep(0.2)
                continue
            loc = self.find_template(template_name, img, threshold=threshold, click=click)
            if loc:
                return loc
            time.sleep(0.2)
        self.image_logger.trace(f"wait_for_template({template_name}) timeout after {tries} tries")
        return None


def is_visible(self, template_name: str, timeout: float = 0.0) -> bool:
        """
        Return True if `template_name` is currently visible on screen.

        Parameters
        ----------
        template_name : str
            Key into self.templates.
        timeout : float, optional
            If > 0, poll for up to this many seconds (delegates to
            wait_for_template).  If 0 (default), takes a single screenshot
            and checks immediately.
        """
        if timeout and timeout > 0:
            return self.wait_for_template(template_name, timeout=timeout, click=False) is not None
        img = self.adb_screenshot()
        return img is not None and (self.find_template(template_name, img, click=False) is not None)


def extract_text_from_roi(self, x1, y1, x2, y2, device=None, psm="7", whitelist=None, save_debug=False):
        """
        Run Tesseract OCR on a rectangular screen region and return the best
        normalised text string found.

        Preprocessing pipeline
        ----------------------
        1. Capture full screen via capture_device_screen(device).
        2. Crop the ROI [y1:y2, x1:x2] (clamped to image bounds).
        3. Convert to grayscale.
        4. Upscale 3× with bicubic interpolation (improves small-text OCR).
        5. Apply CLAHE (contrast-limited adaptive histogram equalisation).
        6. Otsu binarisation; invert if background is dark.
        7. Morphological OPEN to remove salt-and-pepper noise.
        8. Feed both the binarised (bw) and inverted (inv) images to Tesseract.

        Tesseract sweep
        ---------------
        Tries every combination of:
          images  : [bw, inv, gray]
          OEM     : [1 (legacy), 3 (LSTM)]
          PSMs    : [caller’s psm, "13", "6"]
        Returns as soon as any combination produces text matching the
        fraction pattern (r\"\\d+/\\d+\"), normalised to:
            "Today's Trade Count: <used>/<total>"
        If no fraction is found in any attempt, scores all candidate strings
        and returns the normalised version of the highest-scoring one.

        Parameters
        ----------
        x1, y1, x2, y2 : int
            Top-left and bottom-right pixel coordinates of the ROI on the
            full phone screen (1080 × 2160 coordinate space).
        device : str, optional
            ADB device serial.  Defaults to None (uses the first available).
        psm : str, optional
            Primary Tesseract page segmentation mode (default "7" = single
            text line).  "13" and "6" are also always tried as fallbacks.
        whitelist : str, optional
            tessedit_char_whitelist value.  Defaults to alphanumerics + ":/' ".
        save_debug : bool, optional
            If True (or CONFIG["debug_level"] >= 2), logs each OCR candidate
            at DEBUG level.  Does not save image files (that code is commented
            out but left as reference).

        Returns
        -------
        str
            Normalised OCR text, or "" if nothing was extracted.
        """
        if whitelist is None:
            whitelist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:/' "
        img = context.capture_device_screen(device)

        # Clamp and validate box
        h_img, w_img = img.shape[:2]
        x1c = max(0, min(int(x1), w_img - 1))
        y1c = max(0, min(int(y1), h_img - 1))
        x2c = max(0, min(int(x2), w_img))
        y2c = max(0, min(int(y2), h_img))
        if x2c <= x1c or y2c <= y1c:
            return ""

        roi_img = img[y1c:y2c, x1c:x2c]

        scale = 3
        gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if bw.mean() < 127:
            bw = cv2.bitwise_not(bw)
        kernel = np.ones((2, 2), np.uint8)
        bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel, iterations=1)
        inv = cv2.bitwise_not(bw)
        # Save debug artifacts with timestamp in debug_dir
        ocr_debug = bool(save_debug or context.CONFIG.get("debug_level", 1) >= 2)
        # if ocr_debug:
        #     os.makedirs(CONFIG["debug_dir"], exist_ok=True)
        #     ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        #     cv2.imwrite(os.path.join(CONFIG["debug_dir"], f"ocr_roi_{ts}_bw.png"), bw)
        #     cv2.imwrite(os.path.join(CONFIG["debug_dir"], f"ocr_roi_{ts}_inv.png"), inv)
        # --- updated: try OEM 1 and 3, on multiple images and PSMs
        psms = [psm, "13", "6"]
        images = [("bw", bw), ("inv", inv), ("gray", gray)]
        candidates = []
        frac_re = re.compile(r"(\d[\d,]*)\s*/\s*(\d[\d,]*)")
        # Sanitize whitelist to avoid breaking shlex splitting in pytesseract (Linux)
        safe_whitelist = re.sub(r'["\']', '', whitelist or "")
        oems = ["1", "3"]  # legacy and LSTM (winning OEM=3)

        for img_name, im in images:
            for oem in oems:
                for p in psms:
                    cfg_wl = f'--oem {oem} -l eng --psm {p} -c preserve_interword_spaces=1 -c user_defined_dpi=300 -c tessedit_char_whitelist={safe_whitelist}'
                    try:
                        txt = pytesseract.image_to_string(im, config=cfg_wl).strip()
                        if txt:
                            if ocr_debug:
                                self.game_logger.debug(f"OCR try [{img_name}] oem={oem} psm={p} len={len(txt)}")
                            # Early accept if we find a fraction, return normalized
                            m = frac_re.search(txt) or frac_re.search(txt.replace(" ", ""))
                            if m:
                                normalized = f"Counter: {m.group(1)}/{m.group(2)}"
                                if ocr_debug:
                                    self.game_logger.debug(f"OCR winning config [{img_name}] oem={oem} psm={p} -> '{normalized}'")
                                return normalized
                            candidates.append(txt)
                    except Exception as e:
                        if ocr_debug:
                            self.game_logger.debug(f"OCR call failed for [{img_name}] OEM={oem} PSM={p}: {e}.")



        if ocr_debug:
            self.game_logger.debug(f"OCR ROI [{x1}:{y1} -> {x2}:{y2}] candidates: {candidates if candidates else '[]'}")

        wanted_tokens = {"today", "today's", "trade", "count"}
        def score(s: str):
            s_norm = s.lower().replace("’", "'")
            token_score = sum(1 for t in wanted_tokens if t in s_norm)
            frac = 1 if frac_re.search(s_norm) else 0
            letters = sum(ch.isalnum() for ch in s_norm)
            return (token_score, frac, letters, len(s_norm))
        def normalize_ui(s: str):
            s = s.strip()
            s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
            s = re.sub(r"\s+", " ", s)
            m = re.search(r"(today'?s.*)", s, flags=re.I)
            if m:
                s = m.group(1)
            s = re.sub(r"today\s*s", "Today's", s, flags=re.I)
            s = re.sub(r"today'?s\s*trade\s*count", "Today's Trade Count", s, flags=re.I)
            s = re.sub(r"\s*:\s*", ": ", s)
            m2 = frac_re.search(s)
            if m2:
                s = f"Counter: {m2.group(1)}/{m2.group(2)}"
            return s.strip()
        if not candidates:
            if ocr_debug:
                self.game_logger.debug("OCR produced no candidates (empty).")
            return ""

        best_raw = max(candidates, key=score)
        normalized = normalize_ui(best_raw)

        if ocr_debug:
            self.game_logger.debug(f"OCR best_raw: '{best_raw}' -> normalized: '{normalized}'")

        return normalized


class DetectionMixin:
    def _load_templates(self):
        """Load template images from CONFIG['image_paths']."""
        templates = {}
        failed = []
        for name, path in context.CONFIG.get("image_paths", {}).items():
            resolved_path = Path(path).expanduser()
            if not resolved_path.is_absolute():
                resolved_path = context.PROJECT_ROOT / resolved_path
            img = cv2.imread(str(resolved_path), cv2.IMREAD_UNCHANGED)
            if img is None:
                self.image_logger.warning(f"Could not load template image: {resolved_path}")
                failed.append(name)
            else:
                templates[name] = img
        self.image_logger.info(f"Loaded {len(templates)} templates; failed: {failed}")
        return templates

    def _add_to_tpl_cache(self, key, value):
        """Add template to cache with size limit (LRU-like eviction)."""
        if len(self._tpl_cache) >= self._tpl_cache_max_size:
            # Remove oldest 20% of entries when cache is full
            to_remove = len(self._tpl_cache) // 5
            for old_key in list(self._tpl_cache.keys())[:to_remove]:
                del self._tpl_cache[old_key]
        self._tpl_cache[key] = value

    def _locate_by_color(self, cfg: dict, screenshot: np.ndarray | None = None) -> tuple[int, int] | None:
        """
        Generic HSV colour-blob locator.  Returns the centroid of the largest
        matching contour, or None if no blob meets the minimum area threshold.

        Algorithm
        ---------
        1. Optionally crop to cfg["roi"] = [x1, y1, x2, y2] to limit the
           search area and reduce false positives.
        2. Convert the (cropped) frame to HSV colour space.
        3. Build a mask via cv2.inRange() using the centre HSV values and
           per-channel tolerances stored in cfg (h_tol, s_tol, v_tol).
        4. Morphological OPEN removes small noise specks.
        5. Find all external contours; pick the largest one.
        6. If the largest contour's area is below cfg["min_area"], return None.
        7. Return the centroid of that contour translated back to full-image
           coordinates (adds roi offset back in).

        cfg keys
        --------
        hsv        (h, s, v) centre colour in OpenCV HSV space (H 0-179)
        h_tol      hue tolerance (int)
        s_tol      saturation tolerance (int)
        v_tol      value tolerance (int)
        min_area   minimum contour pixel area to accept (int)
        roi        optional [x1, y1, x2, y2] crop rectangle (list, optional)
        """
        img = screenshot if screenshot is not None else self.adb_screenshot()
        if img is None:
            return None

        # Optional ROI crop
        roi = cfg.get("roi")
        ox, oy = 0, 0
        if roi:
            x1, y1, x2, y2 = roi
            h_img, w_img = img.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w_img, x2), min(h_img, y2)
            img = img[y1:y2, x1:x2]
            ox, oy = x1, y1

        h, s, v = cfg["hsv"]
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower = np.array(
            [max(0, h - cfg["h_tol"]), max(0, s - cfg["s_tol"]), max(0, v - cfg["v_tol"])],
            dtype=np.uint8,
        )
        upper = np.array(
            [min(179, h + cfg["h_tol"]), min(255, s + cfg["s_tol"]), min(255, v + cfg["v_tol"])],
            dtype=np.uint8,
        )
        mask = cv2.inRange(hsv_img, lower, upper)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        # Find the largest contiguous blob instead of global centroid
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        best = max(contours, key=cv2.contourArea)
        if cv2.contourArea(best) < cfg["min_area"]:
            return None
        moments = cv2.moments(best)
        if moments["m00"] == 0:
            return None
        cx = int(moments["m10"] / moments["m00"]) + ox
        cy = int(moments["m01"] / moments["m00"]) + oy
        return (cx, cy)

    def _gather_search_panel_visible(self, screenshot: np.ndarray | None = None) -> bool:
        """Detect the light gather-search drawer covering the lower screen."""
        frame = screenshot if screenshot is not None else self.adb_screenshot()
        if frame is None:
            return False
        height = frame.shape[0]
        drawer = frame[int(height * 0.62):int(height * 0.98), :]
        if drawer.size == 0:
            return False
        gray = cv2.cvtColor(drawer, cv2.COLOR_BGR2GRAY)
        light_ratio = float(np.mean(gray > 160))
        self.image_logger.debug("Gather search drawer light ratio: %.3f", light_ratio)
        return light_ratio >= float(context.CONFIG.get("gather_search_panel_light_ratio", 0.50))

    def _locate_gather_march_button(
        self,
        screenshot: np.ndarray | None = None,
    ) -> tuple[int, int] | None:
        """Locate the blue March button in the troop dispatch popup."""
        frame = screenshot if screenshot is not None else self.adb_screenshot()
        if frame is None:
            return None

        x1, y1, x2, y2 = context.CONFIG.get(
            "gather_march_button_roi",
            (250, 1450, 750, 1660),
        )
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return None

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        blue = cv2.inRange(
            hsv,
            np.array([90, 60, 80], dtype=np.uint8),
            np.array([120, 255, 255], dtype=np.uint8),
        )
        blue = cv2.morphologyEx(
            blue,
            cv2.MORPH_CLOSE,
            np.ones((5, 5), dtype=np.uint8),
        )
        contours, _ = cv2.findContours(
            blue,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        for contour in sorted(contours, key=cv2.contourArea, reverse=True):
            area = float(cv2.contourArea(contour))
            x, y, width, height = cv2.boundingRect(contour)
            if area < 15000 or width < 240 or height < 70:
                continue
            center = (x1 + x + width // 2, y1 + y + height // 2)
            self.image_logger.debug(
                "Gather March button found at %s (area=%.0f size=%dx%d).",
                center,
                area,
                width,
                height,
            )
            return center
        return None

    def _endless_night_close_backdrop_visible(
        self,
        screenshot: np.ndarray,
        location: tuple[int, int],
    ) -> bool:
        """Reject white-X matches that do not sit on the event's dark button."""
        template = self.templates.get("endless_night_close")
        if template is None or screenshot is None:
            return False

        x, y = location
        height, width = template.shape[:2]
        patch = screenshot[y:y + height, x:x + width, :3]
        if patch.shape[:2] != (height, width):
            return False

        gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        if template.ndim == 3 and template.shape[2] == 4:
            backdrop_pixels = gray[template[:, :, 3] == 0]
        else:
            backdrop_pixels = gray
        if backdrop_pixels.size == 0:
            return False

        dark_ratio = float(np.mean(backdrop_pixels < 100))
        self.image_logger.debug(
            "Endless Night close backdrop dark ratio: %.3f",
            dark_ratio,
        )
        return dark_ratio >= float(
            context.CONFIG.get("endless_night_close_backdrop_dark_ratio", 0.45)
        )

    def _troop_unit_cap_reached(self, screenshot: np.ndarray | None = None) -> bool:
        """Confirm that the Military Center is full from its warning or counter."""
        frame = screenshot if screenshot is not None else self.adb_screenshot()
        if frame is None:
            return False

        # The current game briefly shows this toast immediately after Train,
        # even when the capacity counter is slightly below its nominal limit.
        toast_path = context.CONFIG["image_paths"].get("troop_unit_cap_toast")
        if toast_path:
            template = cv2.imread(str(context.PROJECT_ROOT / toast_path))
            if template is not None and context._template_match_centers(
                frame, template, (200, 620, 900, 850), threshold=.9, max_matches=1
            ):
                self.game_logger.info("Training refused: Unit Cap reached toast.")
                return True

        capacity_text = context._ocr_frame_text(
            frame,
            tuple(context.CONFIG.get("troop_training_capacity_roi", (60, 1160, 420, 1300))),
            psm=11,
        )
        capacity = context._parse_fraction(capacity_text)
        if capacity is not None and capacity[0] >= capacity[1] > 0:
            self.game_logger.info(
                "Military Center capacity is full before training (%d/%d).",
                capacity[0],
                capacity[1],
            )
            return True

        x1, y1, x2, y2 = context.CONFIG.get(
            "troop_unit_cap_message_roi",
            (150, 900, 930, 1120),
        )
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return False

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        for psm in ("6", "11"):
            try:
                text = pytesseract.image_to_string(
                    gray,
                    config=f"--oem 3 -l eng --psm {psm}",
                ).strip()
            except Exception as exc:
                self.image_logger.debug("Troop unit-cap OCR failed: %s", exc)
                continue
            self.image_logger.debug("Troop unit-cap OCR psm=%s: %r", psm, text)
            if context._is_unit_cap_message(text):
                return True
        return False

    def _ocr_march_roi(self, screenshot: np.ndarray, roi: tuple[int, int, int, int], whitelist: str) -> list[str]:
        """Return OCR candidates for a small march-sidebar ROI."""
        if screenshot is None:
            return []
        h_img, w_img = screenshot.shape[:2]
        x1, y1, x2, y2 = [int(v) for v in roi]
        x1 = max(0, min(x1, w_img - 1))
        y1 = max(0, min(y1, h_img - 1))
        x2 = max(0, min(x2, w_img))
        y2 = max(0, min(y2, h_img))
        if x2 <= x1 or y2 <= y1:
            return []

        crop = screenshot[y1:y2, x1:x2]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants = [gray, blur, bw, cv2.bitwise_not(bw)]
        safe_whitelist = re.sub(r'["\']', "", whitelist or "")
        candidates: list[str] = []

        for image in variants:
            for psm in ("7", "8", "11", "13"):
                cfg = f"--oem 3 -l eng --psm {psm} -c user_defined_dpi=300 -c tessedit_char_whitelist={safe_whitelist}"
                try:
                    raw = pytesseract.image_to_string(image, config=cfg).strip()
                except Exception as e:
                    self.game_logger.debug("March sidebar OCR call failed: %s", e)
                    continue
                if raw:
                    candidates.append(raw)
        return candidates

    def _parse_march_count_from_candidates(self, candidates: list[str]) -> tuple[int, int] | None:
        for raw in candidates:
            compact = re.sub(r"\s+", "", raw)
            match = re.search(r"([0-9])\s*/\s*([0-9])", raw) or re.search(r"([0-9])/([0-9])", compact)
            if not match:
                continue
            used, total = int(match.group(1)), int(match.group(2))
            if 0 <= used <= total <= 6:
                return used, total
        return None

    def _parse_march_duration_from_candidates(self, candidates: list[str]) -> tuple[str, int] | None:
        """
        Parse sidebar duration text such as 29s, 2m, 2h2m.
        Common OCR drift maps trailing 5/3/8 to seconds, e.g. 295 -> 29s.
        """
        for raw in candidates:
            compact = re.sub(r"\s+", "", raw).lower()
            compact = compact.replace("o", "0").replace("i", "1").replace("l", "1")
            compact = re.sub(r"[^0-9hms]", "", compact)
            if not compact:
                continue
            if re.fullmatch(r"\d{2,3}[538]", compact):
                compact = f"{compact[:-1]}s"

            match = re.fullmatch(r"(\d+)h(\d+)m", compact)
            if match:
                hours, minutes = int(match.group(1)), int(match.group(2))
                return f"{hours}h{minutes}m", hours * 3600 + minutes * 60

            match = re.fullmatch(r"(\d+)h", compact)
            if match:
                hours = int(match.group(1))
                return f"{hours}h", hours * 3600

            match = re.fullmatch(r"(\d+)m", compact)
            if match:
                minutes = int(match.group(1))
                return f"{minutes}m", minutes * 60

            match = re.fullmatch(r"(\d+)s", compact)
            if match:
                seconds = int(match.group(1))
                return f"{seconds}s", seconds

            if re.fullmatch(r"\d{1,3}", compact):
                seconds = int(compact)
                if seconds <= 300:
                    return f"{seconds}s", seconds
        return None

    def _march_idle_marker_visible(self, screenshot: np.ndarray, roi: tuple[int, int, int, int]) -> bool:
        """Detect the white Zz marker shown on an idle march slot."""
        if screenshot is None:
            return False
        h_img, w_img = screenshot.shape[:2]
        x1, y1, x2, y2 = [int(v) for v in roi]
        x1 = max(0, min(x1, w_img - 1))
        y1 = max(0, min(y1, h_img - 1))
        x2 = max(0, min(x2, w_img))
        y2 = max(0, min(y2, h_img))
        if x2 <= x1 or y2 <= y1:
            return False
        crop = screenshot[y1:y2, x1:x2]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        bright = int((gray > 210).sum())
        return bright >= 300 and bright / max(gray.size, 1) >= 0.055

    def parse_march_sidebar(self, screenshot: np.ndarray | None = None) -> dict:
        """
        Parse the right-side world-view march sidebar.

        Returns used/total plus one entry per visible slot.  States are:
        marching, idle, gathering, active, or unknown.
        """
        if screenshot is None:
            screenshot = self.adb_screenshot()
        result = {
            "used": None,
            "total": None,
            "active_slots": 0,
            "idle_slots": 0,
            "slots": [],
        }
        if screenshot is None:
            return result

        cfg = context.CONFIG.get("march_sidebar", {})
        count_roi = cfg.get("count_roi")
        if count_roi:
            count = self._parse_march_count_from_candidates(
                self._ocr_march_roi(screenshot, count_roi, "0123456789/")
            )
            if count:
                result["used"], result["total"] = count

        slots = cfg.get("slots", [])
        for index, slot_cfg in enumerate(slots, start=1):
            duration = None
            if slot_cfg.get("time_roi"):
                duration = self._parse_march_duration_from_candidates(
                    self._ocr_march_roi(screenshot, slot_cfg["time_roi"], "0123456789hmsHMS")
                )
            idle = bool(slot_cfg.get("idle_roi") and self._march_idle_marker_visible(screenshot, slot_cfg["idle_roi"]))

            time_text = duration[0] if duration else None
            seconds = duration[1] if duration else None
            if idle and not duration:
                state = "idle"
            elif duration:
                state = "gathering" if seconds is not None and seconds >= 600 else "marching"
            elif idle:
                state = "idle"
            else:
                state = "unknown"

            if state != "idle" and (duration or state in {"gathering", "marching", "active"}):
                result["active_slots"] += 1
            if state == "idle":
                result["idle_slots"] += 1

            result["slots"].append({
                "index": index,
                "state": state,
                "time": time_text,
                "seconds": seconds,
                "idle_marker": idle,
            })

        if result["used"] is None and result["active_slots"]:
            result["used"] = result["active_slots"]
        if result["total"] is None and result["slots"]:
            result["total"] = len(result["slots"])
        return result

    def format_march_sidebar(self, status: dict | None) -> str:
        """Compact human-readable march sidebar summary for logs."""
        if not status:
            return "unknown"
        used = status.get("used")
        total = status.get("total")
        count = f"{used}/{total}" if used is not None and total is not None else "unknown"
        parts = []
        for slot in status.get("slots", []):
            label = slot.get("state", "unknown")
            if slot.get("time"):
                label = f"{label}:{slot['time']}"
            parts.append(f"{slot.get('index')}={label}")
        return f"{count} [{' '.join(parts)}]"

    def march_count(self, status: dict | None) -> tuple[int, int] | None:
        """Return (used, total) from a parsed march sidebar status."""
        if not status:
            return None
        used = status.get("used")
        total = status.get("total")
        if used is None or total is None:
            return None
        return int(used), int(total)

    def read_march_status(self, screenshot: np.ndarray | None = None, *, where: str = "", log: bool = True) -> dict | None:
        """Parse and validate the right-side march sidebar from the current world view."""
        status = self.parse_march_sidebar(screenshot)
        count = self.march_count(status)
        if not count:
            if log:
                self.game_logger.warning("March sidebar status could not be parsed%s.", f" at {where}" if where else "")
            return None

        used, total = count
        if used > total or total <= 0 or total > 6:
            if log:
                self.game_logger.warning(
                    "March sidebar count %s/%s looks invalid%s; skipping this reading.",
                    used,
                    total,
                    f" at {where}" if where else "",
                )
            return None

        if log:
            self.game_logger.info(
                "March sidebar parsed%s: %s",
                f" at {where}" if where else "",
                self.format_march_sidebar(status),
            )
        return status

    def march_slots_full(self, status: dict | None) -> bool:
        """Return True when parsed march status says no march slot is available."""
        count = self.march_count(status)
        if not count:
            return False
        used, total = count
        return total > 0 and used >= total

    def march_dispatch_confirmed(self, before: dict | None, after: dict | None) -> tuple[bool, str]:
        """
        Compare two sidebar readings around a dispatch.

        A dispatch is confirmed when used slots increase, or when an idle slot
        disappears.  If before/after cannot be compared, return False with a
        reason the caller can log or handle.
        """
        before_count = self.march_count(before)
        after_count = self.march_count(after)
        if not before_count:
            return False, "before_unknown"
        if not after_count:
            return False, "after_unknown"

        before_used, before_total = before_count
        after_used, after_total = after_count
        if before_total != after_total:
            return True, "total_changed"
        if after_used > before_used:
            return True, "used_increased"

        before_idle = int(before.get("idle_slots", 0)) if before else 0
        after_idle = int(after.get("idle_slots", 0)) if after else 0
        if before_idle > 0 and after_idle < before_idle:
            return True, "idle_consumed"
        if before_used >= before_total:
            return True, "already_full"
        if before_idle > 0 and after_idle >= before_idle:
            return False, "idle_not_consumed"
        return False, "unchanged"

    def _screen_reference(self, screen_name: str) -> np.ndarray | None:
        """Load and cache a reference screenshot used by screen sanity checks."""
        if screen_name in self._screen_ref_cache:
            return self._screen_ref_cache[screen_name]
        cfg = context.CONFIG.get("screen_sanity", {}).get(screen_name, {})
        path = cfg.get("path", "")
        img = None
        if path:
            candidates = [
                path,
                os.path.join(os.path.dirname(os.path.abspath(__file__)), path),
            ]
            for candidate in candidates:
                img = cv2.imread(candidate)
                if img is not None:
                    break
        if img is None:
            self.image_logger.warning("Screen sanity reference missing for %s: %s", screen_name, path)
        self._screen_ref_cache[screen_name] = img
        return img

    def _roi_similarity(self, current: np.ndarray, reference: np.ndarray, roi: tuple[int, int, int, int]) -> float:
        """Compare the same ROI in two screenshots using normalized correlation."""
        if current is None or reference is None:
            return -1.0
        h_img, w_img = current.shape[:2]
        h_ref, w_ref = reference.shape[:2]
        x1, y1, x2, y2 = [int(v) for v in roi]
        x1 = max(0, min(x1, min(w_img, w_ref) - 1))
        y1 = max(0, min(y1, min(h_img, h_ref) - 1))
        x2 = max(0, min(x2, min(w_img, w_ref)))
        y2 = max(0, min(y2, min(h_img, h_ref)))
        if x2 <= x1 or y2 <= y1:
            return -1.0
        cur = current[y1:y2, x1:x2]
        ref = reference[y1:y2, x1:x2]
        cur_gray = cv2.cvtColor(cur, cv2.COLOR_BGR2GRAY)
        ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
        if cur_gray.std() < 1.0 or ref_gray.std() < 1.0:
            return -1.0
        return float(cv2.matchTemplate(cur_gray, ref_gray, cv2.TM_CCOEFF_NORMED)[0][0])

    def screen_sanity(self, screen_name: str, screenshot: np.ndarray | None = None) -> dict:
        """Score whether the current screenshot looks like one known screen."""
        if screenshot is None:
            screenshot = self.adb_screenshot()
        cfg = context.CONFIG.get("screen_sanity", {}).get(screen_name)
        result = {
            "screen": screen_name,
            "ok": False,
            "score": -1.0,
            "matches": 0,
            "scores": [],
        }
        if screenshot is None or not cfg:
            return result
        ref = self._screen_reference(screen_name)
        if ref is None:
            return result

        threshold = float(cfg.get("threshold", 0.72))
        scores = [self._roi_similarity(screenshot, ref, roi) for roi in cfg.get("rois", [])]
        valid_scores = [s for s in scores if s >= -0.5]
        matches = sum(1 for s in valid_scores if s >= threshold)
        avg = float(sum(valid_scores) / len(valid_scores)) if valid_scores else -1.0
        min_matches = int(cfg.get("min_matches", len(scores) or 1))
        min_avg = float(cfg.get("min_avg", threshold))
        result.update({
            "ok": bool(matches >= min_matches and avg >= min_avg),
            "score": avg,
            "matches": matches,
            "scores": scores,
        })
        return result

    def detect_screen(self, screenshot: np.ndarray | None = None, candidates: list[str] | tuple[str, ...] | None = None) -> dict:
        """Return the best known screen sanity match for a screenshot."""
        if screenshot is None:
            screenshot = self.adb_screenshot()
        names = list(candidates or context.CONFIG.get("screen_sanity", {}).keys())
        checks = [self.screen_sanity(name, screenshot) for name in names]
        if not checks:
            return {"screen": None, "ok": False, "score": -1.0, "checks": []}
        ok_checks = [c for c in checks if c.get("ok")]
        best = max(ok_checks or checks, key=lambda c: (c.get("ok", False), c.get("score", -1.0), c.get("matches", 0)))
        return {
            "screen": best.get("screen") if best.get("ok") else None,
            "ok": bool(best.get("ok")),
            "score": best.get("score", -1.0),
            "matches": best.get("matches", 0),
            "checks": checks,
        }

    def is_screen(self, screen_name: str, screenshot: np.ndarray | None = None, *, log: bool = False) -> bool:
        """Boolean screen sanity check with template/parser fallbacks for base/world."""
        if screenshot is None:
            screenshot = self.adb_screenshot()
        if screenshot is None:
            return False
        sanity = self.screen_sanity(screen_name, screenshot)
        ok = bool(sanity.get("ok"))

        if not ok and screen_name == "home":
            ok = self.find_template("home", screenshot, click=False) is not None
        elif not ok and screen_name == "world":
            # Static world-view controls are both faster and less ambiguous
            # than sidebar OCR.  Checking them first keeps one transition
            # frame from consuming an entire confirmation timeout.
            ok = any(
                self.find_template(tpl, screenshot, click=False) is not None
                for tpl in ("hq", "hq2")
            )
            if not ok:
                status = self.read_march_status(
                    screenshot,
                    where="screen sanity world fallback",
                    log=False,
                )
                ok = status is not None
        elif not ok and screen_name == "radar":
            ok = self.find_template("radar_check", screenshot, click=False) is not None
        elif not ok and screen_name == "chat":
            ok = self.find_template("chat", screenshot, click=False) is not None
        elif not ok and screen_name == "trucks":
            ok = self.find_template("truck", screenshot, click=False) is not None or self._locate_truck_plus(screenshot) is not None

        if log:
            self.game_logger.debug(
                "Screen sanity %s: ok=%s score=%.3f matches=%s scores=%s",
                screen_name,
                ok,
                sanity.get("score", -1.0),
                sanity.get("matches", 0),
                [round(s, 3) for s in sanity.get("scores", [])],
            )
        return bool(ok)
