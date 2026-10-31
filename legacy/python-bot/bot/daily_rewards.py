"""Verified daily VIP claims and personal/ally bounty missions."""
import re
import time
from collections import Counter
import cv2
import pytesseract

from bot.context import context


def _text(frame, roi):
    return context._ocr_frame_text(frame, roi, psm=11).lower()


def _tap(bot, point):
    bot.adb_tap(*point)
    time.sleep(1.5)
    return bot.adb_screenshot()


def _reward(bot, frame):
    frame = _wait_reward(bot, frame)
    if _reward_visible(frame, bot):
        return _tap(bot, (540, 1880))
    return frame


def _wait_reward(bot, frame):
    for _ in range(5):
        if _reward_visible(frame, bot):
            break
        time.sleep(0.8)
        frame = bot.adb_screenshot()
    return frame


def _reward_visible(frame, bot=None):
    if bot is not None and _template_center(bot, 'daily_reward_banner', frame):
        return True
    return any('congratulations' in context._ocr_frame_text(frame, roi, psm=7).lower()
               for roi in ((230, 530, 850, 625), (320, 765, 840, 830)))


def _template_center(bot, name, frame):
    point = bot.find_template(name, frame, click=False)
    if point is None:
        return None
    height, width = bot.templates[name].shape[:2]
    return point[0] + width // 2, point[1] + height // 2


def _vip_panel(frame):
    text = _text(frame, (40, 370, 800, 550))
    return 'vip' in text and ('points' in text or 'streak' in text)


def _vip_cooldown(frame, index):
    x1, y1, x2, y2 = ((870, 495, 1040, 550), (800, 1500, 1020, 1555))[index]
    crop = frame[y1:y2, x1:x2]
    mask = cv2.inRange(cv2.cvtColor(crop, cv2.COLOR_BGR2HSV), (0, 0, 180), (180, 90, 255))
    mask = cv2.resize(255-mask, None, fx=4, fy=4)
    mask = cv2.copyMakeBorder(mask, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=255)
    text = pytesseract.image_to_string(mask, config='--psm 7 -c tessedit_char_whitelist=0123456789:')
    return bool(re.search(r'\b\d{1,2}:[0-5]\d:[0-5]\d\b', text))


def do_vip_rewards(self, game_name):
    """Open VIP regardless of the notification badge; verify both daily claims."""
    if not self.ensure_base_view():
        return False
    try:
        frame = _tap(self, context.CONFIG['vip_rewards']['entry'])
        if not _vip_panel(frame):
            raise RuntimeError('VIP panel was not confirmed')
        claimed = 0
        for index, roi in enumerate(((820, 390, 1040, 570), (730, 1350, 1040, 1650))):
            def claim_target(image):
                if index == 1:
                    return _template_center(self, 'vip_freebies_claim', image)
                return context._find_ocr_word_center(image, 'claim', roi)
            point = claim_target(frame)
            if point:
                result = _wait_reward(self, _tap(self, point))
                if not _reward_visible(result, self):
                    raise RuntimeError('VIP Claim did not produce a reward confirmation')
                # The login-points reward is a modal with a close control;
                # Daily Freebies uses the full-screen reward overlay.
                if 'login streak' in _text(result, (200, 850, 900, 1400)):
                    frame = _tap(self, (910, 798))
                else:
                    frame = _reward(self, result)
                if not _vip_panel(frame) or claim_target(frame):
                    raise RuntimeError('VIP claim remains available after collecting')
                claimed += 1
            elif not _vip_cooldown(frame, index):
                raise RuntimeError('VIP reward is neither claimable nor on a readable cooldown')
        self._record_action(game_name, 'vip_rewards', 'success',
                            f'Both daily VIP rewards verified; collected {claimed}')
        self._mark_daily_action_complete(game_name, 'vip_rewards', 'Both daily rewards collected or on cooldown')
        return True
    except Exception as exc:
        self._record_action(game_name, 'vip_rewards', 'failed', str(exc))
        return False
    finally:
        self.ensure_base_view()


def _bounty_panel(frame):
    text = _text(frame, (15, 40, 650, 150))
    return 'bounty' in text and 'missions' in text


class BountyEntryUnavailable(RuntimeError):
    """Stable HQ has no identifiable entry; not evidence of completed missions."""


def _open_bounties(bot):
    frame = bot.adb_screenshot()
    if _bounty_panel(frame):
        return frame
    point = _template_center(bot, 'bounty_wanted', frame)
    if not point:
        if not bot.ensure_base_view():
            raise RuntimeError('Base view unavailable before opening Wanted')
        frame = bot.adb_screenshot()
        point = _template_center(bot, 'bounty_wanted', frame)
    if not point:
        # Sidebar artwork/layout can change. Use its visible label rather
        # than blindly tapping an old coordinate or opening world hunting.
        for _ in range(2):
            point = context._find_ocr_word_center(frame, 'wanted', (0, 220, 260, 1800))
            if point is None:
                point = context._find_ocr_word_center(frame, 'bounty', (0, 220, 260, 1800))
            if point is not None:
                break
            time.sleep(1)
            frame = bot.adb_screenshot()
            point = _template_center(bot, 'bounty_wanted', frame)
            if point is not None:
                break
        if point is None:
            if frame is None or not bot.ensure_base_view():
                raise RuntimeError('Could not verify HQ while locating Wanted')
            raise BountyEntryUnavailable('Stable HQ has no visible Wanted entry; missions not inspected')
    frame = _tap(bot, point)
    if not _bounty_panel(frame):
        raise RuntimeError('Wanted shortcut did not open Bounty Missions')
    return frame


def _assist_counter(frame):
    text = _text(frame, (670, 530, 1060, 605))
    match = re.search(r'(\d+)\s*/\s*(\d+)', text)
    return tuple(map(int, match.groups())) if match else None


def _pending(frame):
    badge = cv2.cvtColor(frame[625:662, 497:535], cv2.COLOR_BGR2HSV)
    red = cv2.inRange(badge, (0, 100, 80), (12, 255, 255)) | cv2.inRange(badge, (170, 100, 80), (180, 255, 255))
    if cv2.countNonZero(red) / red.size < 0.08:
        return 0  # The available-mission badge disappears when the list is exhausted.
    readings = []
    for roi, psm in (((490, 615, 540, 670), 10), ((500, 630, 530, 657), 6),
                     ((503, 632, 528, 657), 13)):
        x1, y1, x2, y2 = roi
        crop = frame[y1:y2, x1:x2]
        mask = cv2.inRange(cv2.cvtColor(crop, cv2.COLOR_BGR2HSV), (0, 0, 190), (180, 90, 255))
        mask = cv2.resize(255-mask, None, fx=5, fy=5)
        mask = cv2.copyMakeBorder(mask, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
        text = pytesseract.image_to_string(mask, config=f'--psm {psm} -c tessedit_char_whitelist=0123456789')
        match = re.fullmatch(r'\s*(\d{1,2})\s*', text)
        if match:
            readings.append(int(match[1]))
    consensus = Counter(readings).most_common(1)
    return consensus[0][0] if consensus and consensus[0][1] >= 2 else None


def _bounty_button(bot, frame, name, word):
    point = _template_center(bot, name, frame)
    if point and 70 <= point[0] <= 1010 and 780 <= point[1] <= 1920:
        return point
    return context._find_ocr_word_center(frame, word, (70, 780, 1010, 1920))


def do_personal_bounties(self, game_name):
    """Help allies, claim finished missions, and dispatch available personal missions."""
    assisted = claimed = dispatched = 0
    try:
        frame = _open_bounties(self)
        ally_tab = context._find_ocr_word_center(frame, 'ally', (540, 630, 1050, 740))
        if not ally_tab:
            raise RuntimeError('Ally Missions tab was not found')
        frame = _tap(self, ally_tab)
        for _ in range(5):
            counter = _assist_counter(frame)
            if counter is None:
                raise RuntimeError('Assist Ally counter was unreadable')
            if counter[0] >= counter[1]:
                break
            help_point = _bounty_button(self, frame, 'bounty_help', 'help')
            if not help_point:
                break
            frame = _reward(self, _tap(self, help_point))
            after = _assist_counter(frame)
            if not after or after[0] != counter[0] + 1:
                raise RuntimeError('Ally assistance did not increase the daily counter')
            assisted += 1
        self._record_action(game_name, 'bounty_assist', 'success' if assisted else 'unavailable',
                            f'Verified {assisted} ally assists', assisted=assisted)
        personal = context._find_ocr_word_center(frame, 'personal', (50, 630, 540, 740))
        if not personal:
            raise RuntimeError('Personal Missions tab was not found')
        frame = _tap(self, personal)
        skipped = set()
        for _ in range(18):
            if not _bounty_panel(frame):
                raise RuntimeError('Personal bounty list was lost')
            claim = _bounty_button(self, frame, 'bounty_claim', 'claim')
            if claim:
                result = _wait_reward(self, _tap(self, claim))
                if not _reward_visible(result, self):
                    raise RuntimeError('Bounty Claim did not show a reward confirmation')
                frame = _reward(self, result)
                claimed += 1
                continue
            candidates = context._template_match_centers(frame, self.templates.get('bounty_go'),
                (70, 780, 1010, 1920), threshold=0.9, max_matches=9)
            candidates.sort(key=lambda point: (point[1] // 200, point[0]))
            go = next(((x, y) for x, y, _ in candidates if (x // 100, y // 100) not in skipped), None)
            if not go:
                break
            before = _pending(frame)
            if before is None:
                raise RuntimeError('Remaining personal-missions counter was unreadable')
            if before == 0:
                break
            frame = _tap(self, go)
            quick = _template_center(self, 'bounty_quick_deploy', frame)
            if not quick:
                # Some GO cards locate world objectives rather than opening
                # hero dispatch. Leave those alone and try another card.
                skipped.add((go[0] // 100, go[1] // 100))
                self.game_logger.info('Bounty card opened a world objective; trying another personal mission.')
                frame = _open_bounties(self)
                continue
            if 'conditions' not in _text(frame, (70, 1030, 700, 1430)):
                raise RuntimeError('Personal bounty hero-selection screen was not confirmed')
            frame = _tap(self, quick)
            dispatch = _template_center(self, 'bounty_dispatch', frame)
            if not dispatch:
                raise RuntimeError('Bounty Dispatch control was not found')
            frame = _tap(self, dispatch)
            if _template_center(self, 'bounty_quick_deploy', frame):
                raise RuntimeError('Bounty cannot dispatch: heroes unavailable or requirements unmet')
            frame = _open_bounties(self)
            after = _pending(frame)
            if before is None or after is None or after != before - 1:
                raise RuntimeError('Bounty dispatch was not verified by the remaining-missions counter')
            dispatched += 1
            self._record_action(game_name, 'bounty_dispatch', 'success',
                                'Personal mission dispatched; remaining counter decreased by one',
                                remaining=after)
        self._record_action(game_name, 'bounty', 'success' if assisted or claimed or dispatched else 'unavailable',
                            f'Verified bounty actions: sent={dispatched}, claimed={claimed}, assisted={assisted}',
                            dispatched=dispatched, claimed=claimed, assisted=assisted)
        return True
    except BountyEntryUnavailable as exc:
        self._record_action(game_name, 'bounty', 'unavailable', str(exc),
                            dispatched=dispatched, claimed=claimed, assisted=assisted)
        return False
    except Exception as exc:
        self._record_action(game_name, 'bounty', 'failed', str(exc),
                            dispatched=dispatched, claimed=claimed, assisted=assisted)
        return False
    finally:
        self.ensure_base_view()
