"""Protection monitoring and durable Discord notices, independent of Use."""
import datetime as dt
import hashlib
import time
from pathlib import Path
from zoneinfo import ZoneInfo

from bot.context import context


def notice(key, content, files=()):
    from bot import shields
    path = shields._root() / '_health/outbox' / (hashlib.sha256(key.encode()).hexdigest() + '.json')
    if path.exists():
        previous=shields._read(path)
        if not previous.get('resolved_at'):
            return
        archive=shields._root()/'_health/history'/(path.stem+f'-{time.time_ns()}.json')
        shields._save(archive,previous)
    account=key.split(':',1)[0]
    if not files and account in context.CONFIG['shield_activation'].get('accounts',()):
        snapshot=shields._root()/'_health'/account/'latest.png'
        files=[snapshot] if snapshot.is_file() else []
    snapshots=[]
    for index,source in enumerate(map(Path,files)):
        if source.is_file():
            destination=path.with_name(path.stem+f'-{time.time_ns()}-{index}.png')
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(source.read_bytes())
            snapshots.append(str(destination))
    shields._save(path, {'key':key, 'content':content, 'files':snapshots,
                         'created_at':time.time(), 'delivered':False, 'attempts':0})


def cancel(key):
    from bot import shields
    path=shields._root()/'_health/outbox'/(hashlib.sha256(key.encode()).hexdigest()+'.json')
    if path.exists():
        item=shields._read(path)
        if not item.get('delivered') and not item.get('cancelled'):
            item.update(cancelled=True,resolved_at=time.time())
            shields._save(path,item)


def flush(self, now=None):
    from bot import shields
    now = time.time() if now is None else now
    attempted=0
    for path in (shields._root() / '_health/outbox').glob('*.json'):
        try:
            item = shields._read(path)
            if item.get('delivered') or item.get('cancelled') or item.get('next_attempt', 0) > now:
                continue
            if attempted>=2:
                break
            attempted+=1
            files = [(f'shield_evidence_{index+1}.png', p.read_bytes(), 'Shield observation captured for this alert')
                     for index,p in enumerate(map(Path,item.get('files',[]))) if p.is_file()]
            # Save the attempt before network I/O; failures remain queued.
            item['attempts'] += 1
            item['next_attempt'] = now + min(900, 60 * 2 ** min(item['attempts']-1, 4))
            shields._save(path,item)
            sent = context._discord_webhook_post_many(item['content'], shields._webhook(), files,
                timeout=float(context.CONFIG['shield_activation'].get('discord_timeout',15)))
            item['delivered'] = bool(sent)
            item['last_attempt'] = now
            shields._save(path,item)
            self.game_logger.info('Shield notice %s: %s',item['key'],'delivered' if sent else 'queued for retry')
        except Exception as exc:
            self.game_logger.warning('Shield notice delivery pending: %s',exc)


def coverage(account):
    """Most recent live observation wins, including an unreadable observation."""
    from bot import shields
    candidates = []
    for path in (shields._root()/account).glob('*/manifest.json'):
        try:
            saved = shields._read(path)
        except Exception:
            candidates.append({'checked_at':path.stat().st_mtime,'verified':False,'reason':'Unreadable shield transaction record'})
            continue
        if saved.get('state') in ('verified','already_protected') and saved.get('expires_at'):
            candidates.append({'checked_at':saved['expires_at']-saved.get('remaining_seconds',0),
                               'expires_at':saved['expires_at'], 'verified':True})
        elif saved.get('state') in ('uncertain','activation_attempted'):
            candidates.append({'checked_at':saved.get('use_attempted_at',saved.get('started_at',0)),
                               'verified':False,'reason':'Unresolved shield activation'})
    try:
        observed = shields._read(shields._root()/'_health'/f'{account}.json')
    except Exception:
        observed = {'checked_at':0,'verified':False,'reason':'Unreadable coverage observation'}
    if observed:
        candidates.append(observed)
    result=dict(max(candidates,key=lambda value:value['checked_at'])) if candidates else {'checked_at':0,'verified':False,'reason':'No verified protection record'}
    result['last_verified_expiry']=max((value.get('expires_at',0) for value in candidates if value.get('verified')),default=0)
    return result


def _period(local):
    return local.date()-dt.timedelta(days=(local.weekday()-4)%7)


def _monitoring_window(local):
    """Cover the invasion night, not just Saturday's calendar date."""
    return local.weekday() == 5 or (local.weekday() == 6 and local.hour < 6)


def check_coverage(self, accounts, now):
    """Warn through Sunday 06:00 Malta, including DST transitions."""
    from bot import shields
    local = now.astimezone(ZoneInfo('Europe/Malta'))
    if not _monitoring_window(local):
        return
    friday = _period(local)
    saturday = friday + dt.timedelta(days=1)
    target = dt.datetime.combine(saturday+dt.timedelta(days=1),dt.time(4),tzinfo=local.tzinfo).timestamp()
    renewal = dt.datetime.combine(saturday,dt.time(*context.CONFIG['shield_activation'].get('saturday_time',(21,0))),tzinfo=local.tzinfo)
    for account in accounts:
        item = coverage(account)
        stamp = local.isoformat(timespec='seconds')
        if not item.get('verified'):
            last=item.get('last_verified_expiry')
            last_text=dt.datetime.fromtimestamp(last,local.tzinfo).isoformat(timespec='seconds') if last else 'none recorded'
            notice(f'{account}:{friday}:unknown',f'[URGENT Peace Shield] {account}: protection CANNOT BE VERIFIED. '
                   f"{item.get('reason','Live check failed')}. Last verified expiry Malta: {last_text}. Do not assume overnight protection. Checked Malta: {stamp}")
            continue
        expiry = item['expires_at']
        left = expiry-now.timestamp()
        expiry_text = dt.datetime.fromtimestamp(expiry,local.tzinfo).isoformat(timespec='seconds')
        stage = 'expired' if left <= 0 else '10m' if left <= 600 else '30m' if left <= 1800 else '60m' if left <= 3600 else None
        if stage:
            notice(f'{account}:{friday}:expiry:{stage}',f'[URGENT Peace Shield] {account}: '
                   f'{"EXPIRED" if left <= 0 else "expires within " + stage}. Expiry Malta: {expiry_text}. '
                   f'Overnight protection requires attention. Checked: {stamp}')
        if local >= renewal+dt.timedelta(minutes=10) and expiry < target:
            notice(f'{account}:{friday}:overnight-gap',f'[URGENT Peace Shield] {account}: overnight coverage is INCOMPLETE. '
                   f'Current shield expires Malta {expiry_text}; scheduled 8h protection has not been verified through reset. Checked: {stamp}')
        if expiry >= target and left > 3600 and local >= renewal:
            resolved=False
            for path in (shields._root()/'_health/outbox').glob('*.json'):
                item=shields._read(path)
                if item['key'].startswith(f'{account}:{friday}') and not item['key'].endswith(':restored'):
                    if not item.get('resolved_at'):
                        resolved = resolved or item.get('delivered',False)
                        item.update(resolved_at=now.timestamp())
                        if not item.get('delivered'):
                            item['cancelled']=True
                        shields._save(path,item)
            if resolved:
                notice(f'{account}:{friday}:restored',f'[Peace Shield] {account}: protection restored/verified through {expiry_text} Malta.')


def audit_one(self, accounts, now):
    """Bounded live check of one due account; returns whether foreground changed."""
    from bot import shields
    from bot.shield_ui import BuffShieldUI
    if not _monitoring_window(now.astimezone(ZoneInfo('Europe/Malta'))):
        return False
    interval = float(context.CONFIG['shield_activation'].get('health_check_interval',900))
    for account in accounts:
        if now.timestamp()-coverage(account)['checked_at'] < interval:
            continue
        if (shields._root()/account/'activation.lock').exists():
            continue
        observed = {'checked_at':now.timestamp(), 'verified':False}
        try:
            if not self.launch_game(account):
                raise RuntimeError('Could not open account for independent shield check')
            ui = BuffShieldUI(self,context.CONFIG['shield_activation'])
            for path in (shields._root()/account).glob('*/manifest.json'):
                try:
                    if shields._read(path).get('state') in ('uncertain','activation_attempted'):
                        shields.reconcile_shield_attempt(self,account,path,ui=ui)
                except Exception as exc:
                    self.game_logger.warning('Shield transaction unreadable; continuing independent live timer check: %s',exc)
            frame,remaining = ui.timer()
            at = time.time()
            folder = shields._root()/'_health'/account
            folder.mkdir(parents=True,exist_ok=True)
            import cv2
            cv2.imwrite(str(folder/'latest.png'),frame)
            observed.update(checked_at=at, verified=True, expires_at=at+remaining, remaining_seconds=remaining)
            self._record_action(account,'shield_coverage','success','Independent live shield countdown verified',remaining_seconds=remaining)
        except Exception as exc:
            observed['reason'] = str(exc)
            self._record_action(account,'shield_coverage','failed',str(exc))
        finally:
            shields._save(shields._root()/'_health'/f'{account}.json',observed)
            try:
                self.ensure_base_view()
            except Exception:
                self.game_logger.warning('Shield audit could not return to base for %s',account)
        return True
    return False


def rollout_summary(accounts, now):
    from bot import shields
    local = now.astimezone(ZoneInfo('Europe/Malta'))
    friday = _period(local)
    cfg = context.CONFIG['shield_activation']
    for hours,day,timing in ((24,friday,cfg.get('friday_time',(23,0))),
                             (8,friday+dt.timedelta(days=1),cfg.get('saturday_time',(21,0)))):
        due = dt.datetime.combine(day,dt.time(*timing),tzinfo=local.tzinfo)
        if not due <= local <= due+dt.timedelta(hours=8):
            continue
        rows=[]; all_done=True
        for account in accounts:
            try:
                saved = shields._read(shields._root()/account/f'{friday}-{hours}h/manifest.json')
            except Exception:
                saved = {}
            live=coverage(account)
            valid = (saved.get('state') in ('verified','already_protected') and saved.get('expires_at',0)>now.timestamp()
                     and live.get('verified') and live.get('expires_at',0)>=saved.get('expires_at',0)-180)
            all_done = all_done and valid
            expiry = dt.datetime.fromtimestamp(saved['expires_at'],local.tzinfo).isoformat(timespec='seconds') if valid else 'NOT VERIFIED — manual attention required'
            rows.append(f'{account}: {expiry}')
        if all_done or local >= due+dt.timedelta(minutes=10):
            status = 'ALL FOUR VERIFIED' if all_done and len(accounts)==4 else 'ALL VERIFIED' if all_done else 'INCOMPLETE — farms may be exposed overnight'
            if all_done:
                cancel(f'summary:{friday}:{hours}:False')
            notice(f'summary:{friday}:{hours}:{all_done}',f'[Peace Shield rollout] {hours}h — {status}\n'+'\n'.join(rows)+f'\nObserved Malta: {local.isoformat(timespec="seconds")}')


def monitor(self, accounts, now):
    """Run even when all activation transactions are fenced or already complete."""
    cfg=context.CONFIG['shield_activation']
    if not cfg.get('health_enabled',False):
        flush(self,now.timestamp())
        return False
    changed=audit_one(self,accounts,now)
    fresh=dt.datetime.now(dt.timezone.utc)
    check_coverage(self,accounts,fresh)
    rollout_summary(accounts,fresh)
    flush(self,fresh.timestamp())
    return changed
