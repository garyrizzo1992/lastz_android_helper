"""Own a temporary bot-service pause while a Windows SSH client sends heartbeats."""
import fcntl
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

LABEL = 'com.garyrizzo.lastz'
DOMAIN = f'gui/{os.getuid()}'
SERVICE = f'{DOMAIN}/{LABEL}'
PLIST = Path.home() / 'Library' / 'LaunchAgents' / f'{LABEL}.plist'
LOCK = Path.home() / '.local' / 'share' / 'lastz-remote-phone' / 'session.lock'
HEARTBEAT_TIMEOUT = 30


def launchctl(*args):
    return subprocess.run(['/bin/launchctl', *args], capture_output=True, text=True, timeout=15)


def running():
    return launchctl('print', SERVICE).returncode == 0


def interrupted(signum, frame):
    raise SystemExit(f'signal {signum}')


def main():
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open('a+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('ERROR: Another remote-phone session already owns the bot pause.')
        if not PLIST.is_file():
            raise SystemExit('ERROR: Bot LaunchAgent plist was not found.')
        was_loaded = running()
        pause_requested = False
        for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, interrupted)
        try:
            if was_loaded:
                # Set ownership before bootout, so interruption cannot strand the service.
                pause_requested = True
                result = launchctl('bootout', SERVICE)
                if result.returncode:
                    raise RuntimeError('Could not stop bot: ' + result.stderr.strip())
                if running():
                    raise RuntimeError('Bot service is still loaded after stop.')
            print('READY PAUSED' if was_loaded else 'READY ALREADY_STOPPED', flush=True)
            deadline = time.monotonic() + HEARTBEAT_TIMEOUT
            while True:
                ready, _, _ = select.select([sys.stdin], [], [], max(0, deadline - time.monotonic()))
                if not ready:
                    print('Heartbeat expired; restoring previous bot state.', flush=True)
                    break
                command = sys.stdin.readline()
                if not command or command.strip() == 'QUIT':
                    break
                if command.strip() == 'PING':
                    deadline = time.monotonic() + HEARTBEAT_TIMEOUT
        finally:
            # Ignore further disconnect/termination signals while restoring the service.
            for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, signal.SIG_IGN)
            if pause_requested:
                last_error = ''
                for attempt in range(3):
                    if running():
                        break
                    result = launchctl('bootstrap', DOMAIN, str(PLIST))
                    last_error = result.stderr.strip()
                    if result.returncode == 0:
                        break
                    time.sleep(2)
                if not running():
                    raise RuntimeError('BOT RESUME FAILED: ' + last_error)
                print('RESTORED BOT_SERVICE', flush=True)
            else:
                print('RESTORED ALREADY_STOPPED', flush=True)


if __name__ == '__main__':
    main()
