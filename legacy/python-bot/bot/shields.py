"""Disarmed weekly shield activation with durable evidence and Discord outbox.

No work is performed until both enabled and ui_calibrated are explicitly set.
An uncertain Use attempt is fenced against automatic repeat consumption.
"""
import datetime as dt
import json
import os
from pathlib import Path
import time
from zoneinfo import ZoneInfo
import cv2
from bot.context import context
from bot.shield_ui import ShieldUIError, BuffShieldUI


STAGES = (("before", "01_before_inventory.png", "1. Inventory BEFORE activation"),
          ("after", "02_after_inventory.png", "2. Inventory AFTER activation"),
          ("timer", "03_shield_timer.png", "3. Active shield countdown"))


def _root():
    return Path(context.CONFIG["shield_state_dir"])


def _save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)
    if os.name != "nt":
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _read(path):
    if not path.exists():
        return {}
    # Corrupt transaction state must block, not be mistaken for no previous Use.
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ShieldUIError("Invalid saved shield transaction")
    return value


def _webhook():
    # Deliberately no fallback to the general log channel.
    return (context.CONFIG.get("discord_treasures_webhook", "").strip()
            or os.environ.get("DISCORD_TREASURES_WEBHOOK_URL", "").strip())


def _blocked(self, account, hours, operation, reason):
    from bot.shield_health import notice, coverage
    path = _root()/account/operation/'manifest.json'
    saved = _read(path)
    if saved.get('state') not in ('verified','already_protected','uncertain','activation_attempted'):
        _save(path,dict(account=account,hours=hours,operation=operation,state='blocked',reason=reason,
                       started_at=time.time(),screenshots={},discord_delivered=False))
    last=coverage(account).get('last_verified_expiry')
    deadline=dt.datetime.fromtimestamp(last,ZoneInfo('Europe/Malta')).isoformat(timespec='seconds') if last else 'none recorded'
    evidence=[p for p in (_root()/account).glob('*/03_shield_timer.png') if time.time()-p.stat().st_mtime<600]
    evidence.sort(key=lambda p:p.stat().st_mtime,reverse=True)
    notice(f'{account}:{operation}:blocked',f'[URGENT Peace Shield] {account}: scheduled {hours}h shield BLOCKED. '
           f'{reason}. Overnight protection is NOT confirmed; manual attention required. '
           f'Last verified expiry Malta: {deadline}. '
           f'Observed Malta: {dt.datetime.now(ZoneInfo("Europe/Malta")).isoformat(timespec="seconds")}',files=evidence[:1])
    self._record_action(account,'peace_shield','blocked',reason)


def reconcile_shield_attempt(self, account, path, ui=None, force=False):
    """Read-only recovery: a previous Use is never repeated to verify it."""
    saved = _read(path)
    if saved.get('state') not in ('uncertain','activation_attempted'):
        return saved.get('state') in ('verified','already_protected','expired_unverified')
    cfg = context.CONFIG['shield_activation']
    if not force and time.time()-saved.get('last_reconciliation',0) < cfg.get('retry_seconds',300):
        return False
    backup=path.with_name('manifest.before-reconciliation.json')
    if not backup.exists():
        _save(backup,saved)
    saved['last_reconciliation']=time.time()
    _save(path,saved)
    try:
        if ui is None:
            if not self.launch_game(account):
                raise ShieldUIError('Cannot open account to reconcile protection')
            ui=BuffShieldUI(self,cfg)
        timer,remaining=ui.timer()
        observed=time.time()
        after,count,_=ui.inventory(saved['hours'],frame=timer)
        _capture(path.parent,saved,'after',after)
        _capture(path.parent,saved,'timer',timer)
        expected_expiry=saved['use_attempted_at']+saved['hours']*3600
        tolerance=int(cfg.get('timer_tolerance_seconds',180))
        if observed > expected_expiry+tolerance:
            saved.update(state='expired_unverified',remaining_seconds=0,expires_at=None,
                         observed_current_remaining=remaining,
                         reason='Maximum possible duration of the previous ambiguous activation has elapsed. A fresh live timer was read; historical consumption remains unverified. This old operation will not be repeated.',
                         discord_delivered=False)
        else:
            if count != saved.get('before_count',-1)-1 or remaining <= 0 or abs(observed+remaining-expected_expiry)>tolerance:
                raise ShieldUIError('Inventory and live expiry do not prove the previous Use')
            # Require a second fresh timer, not one potentially transient frame.
            timer,second=ui.timer()
            at=time.time()
            if second <= 0 or abs(at+second-expected_expiry)>tolerance:
                raise ShieldUIError('Fresh shield expiry did not confirm recovery')
            _capture(path.parent,saved,'timer',timer)
            saved.update(state='verified',after_count=count,remaining_seconds=second,expires_at=at+second,
                         inventory_delta_verified=True,discord_delivered=False,
                         reason='Recovered previous activation using inventory decrement and two fresh timers matching its original expiry; no additional shield consumed')
        _save(path,saved)
        try:
            _deliver(self,path.parent,saved)
        except Exception as exc:
            self.game_logger.warning('Reconciled shield evidence delivery remains pending: %s',exc)
        return True
    except Exception as exc:
        self.game_logger.warning('Shield reconciliation pending for %s: %s',account,exc)
        return False


def _capture(folder, manifest, stage, frame):
    if frame is None:
        raise ShieldUIError("Missing " + stage + " evidence screenshot")
    name = next(name for key, name, _ in STAGES if key == stage)
    if not cv2.imwrite(str(folder / name), frame):
        raise ShieldUIError("Cannot save " + stage + " evidence screenshot")
    manifest.setdefault("screenshots", {})[stage] = name
    manifest.setdefault("captured_at", {})[stage] = dt.datetime.now(dt.timezone.utc).isoformat()
    _save(folder / "manifest.json", manifest)


def _deliver(self, folder, manifest):
    if manifest.get("discord_delivered"):
        return True
    files = []
    for stage, filename, caption in STAGES:
        if stage in manifest.get("screenshots", {}) and (folder / filename).is_file():
            files.append((filename, (folder / filename).read_bytes(), caption))
    verified = manifest["state"] in {"verified", "already_protected"}
    prefix = "VERIFIED" if verified else "NOT VERIFIED - manual attention required"
    remaining = manifest.get("remaining_seconds")
    expiry = manifest.get("expires_at")
    label = context.CONFIG.get("game_settings", {}).get(manifest["account"], {}).get("label", manifest["account"])
    content = (f"[Peace Shield] {manifest['account']} ({label}) - {manifest['hours']}h - {prefix}\n"
               f"Run: {manifest['operation']}\n{manifest.get('reason', '')}")
    if manifest.get("started_at"):
        content += "\nCaptured (Europe/Malta): " + dt.datetime.fromtimestamp(
            manifest["started_at"], ZoneInfo("Europe/Malta")).isoformat(timespec="seconds")
    if remaining is not None:
        content += f"\nVerified remaining: {remaining // 3600:02d}:{remaining % 3600 // 60:02d}:{remaining % 60:02d}"
    if expiry:
        content += "\nExpires (Europe/Malta): " + dt.datetime.fromtimestamp(expiry, ZoneInfo("Europe/Malta")).isoformat(timespec="seconds")
    sent = context._discord_webhook_post_many(content, _webhook(), files,
                                             timeout=float(context.CONFIG.get("shield_activation", {}).get("discord_timeout", 15)))
    manifest["discord_delivered"] = bool(sent)
    manifest["last_delivery_attempt"] = time.time()
    _save(folder / "manifest.json", manifest)
    self._record_action(manifest["account"], "shield_evidence_delivery", "success" if sent else "failed",
                        "Grouped shield evidence delivered" if sent else "Evidence retained locally; Discord delivery pending",
                        manifest=str(folder / "manifest.json"))
    return sent


def shield_protection_active(self, account):
    """Treat uncertain consumption as protected too: avoid breaking a possible shield."""
    for path in (_root() / account).glob("*/manifest.json"):
        try:
            saved = _read(path)
            if saved.get("state") in {"activation_attempted", "uncertain"}:
                return True
            if saved.get("expires_at", 0) > time.time():
                return True
        except Exception:
            return True
    return False


def do_activate_peace_shield(self, account, hours, operation):
    cfg = context.CONFIG.get("shield_activation", {})
    if not cfg.get("enabled", False) or not cfg.get("ui_calibrated", False):
        return False
    if account not in cfg.get("accounts", ()) or hours not in (8, 24):
        raise ValueError("Invalid shield account or duration")
    folder = _root() / account
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder / "activation.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        _blocked(self,account,hours,operation,'Shield activation lock exists; verify no previous attempt is running')
        return False
    try:
        os.close(descriptor)
        return _activate_locked(self, account, hours, operation)
    finally:
        lock.unlink(missing_ok=True)


def _activate_locked(self, account, hours, operation):
    cfg = context.CONFIG.get("shield_activation", {})
    if not cfg.get("enabled", False) or not cfg.get("ui_calibrated", False):
        return False
    if account not in cfg.get("accounts", ()) or hours not in (8, 24):
        raise ValueError("Invalid shield account or duration")
    # Operation keys are generated by the scheduler, never arbitrary paths.
    day, separator, suffix = operation.rpartition("-")
    if not separator or suffix != f"{hours}h" or dt.date.fromisoformat(day).isoformat() != day:
        raise ValueError("Invalid shield operation key")
    folder = _root() / account / operation
    path = folder / "manifest.json"
    saved = _read(path)
    if saved.get("state") in {"verified", "already_protected"}:
        if not saved.get("discord_delivered"):
            _deliver(self, folder, saved)
        return True
    if saved.get("state") in {"activation_attempted", "uncertain"}:
        if reconcile_shield_attempt(self,account,path):
            return _read(path).get('state') in ('verified','already_protected')
        _blocked(self,account,hours,operation,'Previous shield Use remains uncertain after read-only recovery')
        return False
    # Refuse consumption if there is nowhere to send the requested evidence.
    if not _webhook():
        _blocked(self,account,hours,operation,'Treasure-channel Discord webhook is missing')
        return False
    # A previous uncertain attempt, including one from an earlier week, needs
    # reconciliation before any further inventory consumption on this account.
    for other in (_root() / account).glob("*/manifest.json"):
        if (_read(other).get("state") in {"activation_attempted", "uncertain"}
                and not reconcile_shield_attempt(self,account,other)):
            _blocked(self,account,hours,operation,'Unreconciled shield attempt exists; no item consumed')
            return False
    manifest = {"account": account, "hours": hours, "operation": operation,
                "state": "prepared", "screenshots": {}, "started_at": time.time(),
                "discord_delivered": False}
    _save(path, manifest)
    ui = BuffShieldUI(self, cfg)
    try:
        if not self.launch_game(account):
            raise ShieldUIError("Account launch/base confirmation failed")
        prior_frame, prior_remaining = ui.timer()
        manifest["prior_remaining_seconds"] = prior_remaining
        before, before_count, detail = ui.inventory(hours, frame=prior_frame)
        manifest["before_count"] = before_count
        _capture(folder, manifest, "before", before)
        if prior_remaining >= hours * 3600 - int(cfg.get("timer_tolerance_seconds", 180)):
            # Keep the existing protection; do not consume another item.
            _capture(folder, manifest, "after", ui.inventory_view())
            timer, remaining = ui.timer()
            _capture(folder, manifest, "timer", timer)
            if remaining < hours * 3600 - int(cfg.get("timer_tolerance_seconds", 180)):
                raise ShieldUIError("Existing protection changed during verification")
            manifest.update(state="already_protected", remaining_seconds=remaining,
                            expires_at=time.time() + remaining, reason="Existing shield already covers requested duration; no item used")
        else:
            if before_count < 1:
                raise ShieldUIError("No requested shield in inventory")
            # Normal Saturday renewals stay conservative and only replace a
            # nearly expired shield. An explicitly scheduled 8h rollout is
            # operator-authorized to extend a shorter active shield (for
            # example, replacing the final two hours with eight hours).
            if (hours == 8 and not cfg.get("one_off_8h_start_at") and not cfg.get("saturday_time")
                    and prior_remaining > int(cfg.get("replacement_lead_seconds", 1800))):
                raise ShieldUIError("Refusing to shorten a shield with substantial time remaining")
            # Durable fence BEFORE Use. A crash here requires review, never another blind tap.
            manifest.update(state="activation_attempted", use_attempted_at=time.time())
            _save(path, manifest)
            self._shield_failure_frame=None
            ui.activate(hours, detail, replacing=prior_remaining > 0)
            after_frame = ui.inventory_view()
            _capture(folder, manifest, "after", after_frame)
            try:
                _, after_count, _ = ui.inventory(hours, frame=after_frame)
            except ShieldUIError:
                after_count = None  # preserve the timer evidence before failing inventory proof
            manifest["after_count"] = after_count
            timer, remaining = ui.timer()
            _capture(folder, manifest, "timer", timer)
            expected = hours * 3600
            tolerance = int(cfg.get("timer_tolerance_seconds", 180))
            if not expected - tolerance <= remaining <= expected + 60:
                raise ShieldUIError("Active shield countdown does not match requested duration")
            # Require both independent post-conditions: matching countdown and
            # exactly one fewer item, including Owned: 0 for the final shield.
            if after_count is None:
                raise ShieldUIError("Final Owned count is unreadable; timer captured but inventory proof needs review")
            if after_count != before_count - 1:
                raise ShieldUIError("Inventory did not decrease by exactly one shield")
            manifest.update(state="verified", remaining_seconds=remaining, expires_at=time.time() + remaining,
                            inventory_delta_verified=True,
                            reason="Activation and countdown verified; inventory decreased by one")
        _save(path, manifest)
        self._record_action(account, "peace_shield", "success", manifest["reason"],
                            expires_at=manifest["expires_at"], manifest=str(path))
    except Exception as exc:
        attempted = bool(manifest.get("use_attempted_at"))
        manifest.update(state="uncertain" if attempted else "blocked", reason=str(exc))
        _save(path, manifest)
        if attempted:
            try:
                failure=getattr(self,'_shield_failure_frame',None)
                if failure is None:
                    failure=ui.frame()
                if cv2.imwrite(str(folder/'failure.png'),failure):
                    manifest['failure_screenshot']='failure.png'
                    _save(path,manifest)
            except Exception:
                self.game_logger.warning('Could not capture the shield failure screen for %s',account)
        # Preserve fresh evidence and attempt proof-based recovery even when
        # UI confirmation parsing failed after the item was consumed.
        if attempted:
            reconcile_shield_attempt(self,account,path,ui=ui,force=True)
            manifest=_read(path)
        if manifest['state'] not in ('verified','already_protected'):
            from bot.shield_health import notice
            notice(f'{account}:{operation}:failed',f'[URGENT Peace Shield] {account}: {hours}h activation NOT VERIFIED. '
                   f'{manifest["reason"]}. Protection may lapse overnight; action required.',
                   files=[folder/'failure.png'])
        self._record_action(account, "peace_shield", "success" if manifest['state'] in ('verified','already_protected') else "failed" if attempted else "blocked",
                            manifest["reason"], manifest=str(path))
    finally:
        try:
            self.ensure_base_view()
        except Exception:
            self.game_logger.warning("Shield workflow could not return to base for %s.", account)
    _deliver(self, folder, manifest)
    return manifest["state"] in {"verified", "already_protected"}


def shield_operations(now, cfg, account):
    """Resolve dated overrides or weekly Malta shield operations."""
    local = now.astimezone(ZoneInfo("Europe/Malta"))
    explicit_8h = cfg.get("one_off_8h_start_at")
    if explicit_8h:
        start_8h = dt.datetime.fromisoformat(explicit_8h)
        if start_8h.tzinfo is None or start_8h.utcoffset() is None:
            raise ValueError("8h shield start time requires an explicit timezone offset")
        start_8h = start_8h.astimezone(local.tzinfo)
        if not (start_8h <= local <= start_8h + dt.timedelta(hours=1)):
            return None
        accounts_8h = cfg.get("rollout_8h_accounts") or cfg.get("accounts", ())
        if account in accounts_8h:
            friday_8h = start_8h.date() - dt.timedelta(days=(start_8h.weekday() - 4) % 7)
            return 8, f"{friday_8h}-8h"
    override = cfg.get("one_off_start_at")
    if override:
        start = dt.datetime.fromisoformat(override)
        if start.tzinfo is None or start.utcoffset() is None:
            raise ValueError("Shield start time requires an explicit timezone offset")
        start = start.astimezone(local.tzinfo)
        friday = start.date() - dt.timedelta(days=(start.weekday() - 4) % 7)
    else:
        friday = local.date() - dt.timedelta(days=(local.weekday() - 4) % 7)
        start = dt.datetime.combine(friday, dt.time(*cfg.get("friday_time", (22, 15))), tzinfo=local.tzinfo)
    key24, key8 = f"{friday}-24h", f"{friday}-8h"
    # Bound catch-up to before the stated Saturday invasion reset.
    deadline = dt.datetime.combine(friday + dt.timedelta(days=1), dt.time(3, 30), tzinfo=local.tzinfo)
    if override:
        if start.weekday() not in (4, 5) or (start.weekday() == 4 and start.hour < 22) or start > deadline:
            raise ValueError("Shield start must be Friday evening or before Saturday 03:30 Malta")
        deadline = min(deadline, start + dt.timedelta(hours=1))
    if start <= local <= deadline:
        return (24, key24) if account in cfg.get("rollout_accounts", cfg.get("accounts", ())) else None
    if cfg.get("saturday_time") and cfg.get("saturday_renewal_enabled", False):
        saturday = dt.datetime.combine(friday + dt.timedelta(days=1),
                                       dt.time(*cfg["saturday_time"]), tzinfo=local.tzinfo)
        if saturday <= local <= saturday + dt.timedelta(hours=1):
            return 8, key8
        return None
    if local.weekday() in (5, 6) and cfg.get("saturday_renewal_enabled", False):
        saved = _read(_root() / account / key24 / "manifest.json")
        expiry = saved.get("expires_at")
        if saved.get("state") in {"verified", "already_protected"} and expiry:
            if expiry - cfg.get("replacement_lead_seconds", 1800) <= local.timestamp() <= expiry + 3600:
                return 8, key8
    return None


def shield_start_delay(cfg, now=None):
    """Hold normal rotation briefly so a near-term rollout starts on time."""
    if not all(cfg.get(gate, False) for gate in
               ("enabled", "ui_calibrated", "schedule_enabled")):
        return 0
    starts = [value for value in (cfg.get("one_off_start_at"), cfg.get("one_off_8h_start_at")) if value]
    now = now or dt.datetime.now(dt.timezone.utc)
    if not starts:
        local = now.astimezone(ZoneInfo("Europe/Malta"))
        for weekday, timing in ((4, cfg.get("friday_time", (23, 0))),
                                (5, cfg.get("saturday_time"))):
            if timing and (weekday == 4 or cfg.get("saturday_renewal_enabled", False)):
                date = local.date() + dt.timedelta(days=(weekday-local.weekday()) % 7)
                starts.append(dt.datetime.combine(date, dt.time(*timing), tzinfo=local.tzinfo).isoformat())
    delays = []
    for value in starts:
        start = dt.datetime.fromisoformat(value)
        if start.tzinfo is None or start.utcoffset() is None:
            raise ValueError("Shield start time requires an explicit timezone offset")
        delay = start.timestamp() - now.timestamp()
        if 0 < delay <= 600:
            delays.append(delay)
    return min(delays, default=0)


def process_scheduled_shields(self, accounts, now=None):
    cfg = context.CONFIG.get("shield_activation", {})
    if (not cfg.get("enabled", False) or not cfg.get("ui_calibrated", False)
            or not cfg.get("schedule_enabled", False)):
        return False
    now = now or dt.datetime.now(dt.timezone.utc)
    touched = False
    for account in accounts:
        if account not in cfg.get("accounts", ()):
            continue
        try:
            operation = shield_operations(now, cfg, account)
            if operation is None:
                continue
            hours, key = operation
            saved = _read(_root() / account / key / "manifest.json")
            if saved.get("state") in {"verified", "already_protected", "expired_unverified"}:
                continue
            if now.timestamp() - max(saved.get("started_at", 0),saved.get('last_reconciliation',0)) < cfg.get("retry_seconds", 300):
                continue
            touched = True
            self.do_activate_peace_shield(account, hours, key)
        except Exception as exc:
            self._record_action(account, "peace_shield", "failed", "Shield scheduling failed: " + str(exc))
            from bot.shield_health import notice
            notice(f'{account}:{now.date()}:scheduler-error',f'[URGENT Peace Shield] {account}: scheduling failed: {exc}. Overnight protection cannot be assumed.')
    # Outbox retries never invoke inventory navigation or Use.
    for account in accounts:
        for path in (_root() / account).glob("*/manifest.json"):
            try:
                saved = _read(path)
                if not saved.get("discord_delivered") and now.timestamp() - saved.get("last_delivery_attempt", 0) >= cfg.get("report_retry_seconds", 300):
                    _deliver(self, path.parent, saved)
            except Exception:
                self.game_logger.warning("Shield evidence delivery remains pending for %s.", account)
    from bot.shield_health import monitor
    try:
        touched=monitor(self,accounts,now) or touched
    except Exception as exc:
        self.game_logger.error('Independent shield monitor failed: %s',exc)
        from bot.shield_health import notice, flush
        notice(f'monitor:{now.date()}:failed',f'[URGENT Peace Shield] Coverage monitoring failed: {exc}. Check all farms manually.')
        flush(self,now.timestamp())
    return touched
