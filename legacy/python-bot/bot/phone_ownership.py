"""Shared phone ownership with the native helper. No independent input after lease loss."""
import atexit
import json
import queue
import shlex
import subprocess
import threading
import time
import uuid


class OwnershipLost(RuntimeError):
    pass


class PhoneOwnership:
    def __init__(self, adb, serial):
        self._token = uuid.uuid4().hex
        self._lock = threading.Lock()
        self._messages = queue.Queue(maxsize=64)
        self._closed = threading.Event()
        found = subprocess.run([adb, '-s', serial, 'shell', 'pm', 'path', 'dev.codex.lastzhelper'],
                               capture_output=True, text=True, timeout=5, check=True)
        paths = [line[len('package:'):] for line in found.stdout.splitlines() if line.startswith('package:')]
        if len(paths) != 1:
            raise OwnershipLost('Install the matching native helper before running this Python controller.')
        command = 'CLASSPATH=' + shlex.quote(paths[0]) + ' app_process /system/bin dev.codex.lastzhelper.LegacyLease ' + self._token
        self._process = subprocess.Popen([adb, '-s', serial, 'shell', 'su -c ' + shlex.quote(command)],
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
        threading.Thread(target=self._reader, daemon=True).start()
        try:
            ready = self._messages.get(timeout=8)
            if not ready.get('ok') or ready.get('token') != self._token:
                raise OwnershipLost('Phone is owned by another controller or needs input reconciliation.')
        except Exception:
            self.close()
            raise
        atexit.register(self.close)
        threading.Thread(target=self._heartbeat, daemon=True).start()

    def _reader(self):
        try:
            for line in self._process.stdout:
                try:
                    record = json.loads(line)
                except (ValueError, TypeError):
                    continue
                if not self._closed.is_set():
                    self._messages.put_nowait(record)
        except (OSError, queue.Full):
            pass
        finally:
            self._closed.set()

    def _request(self, action, **values):
        with self._lock:
            if self._closed.is_set() or self._process.poll() is not None:
                raise OwnershipLost('Phone ownership ended; no more Python input is allowed.')
            nonce = uuid.uuid4().hex
            try:
                request = dict(values, action=action, nonce=nonce, token=self._token)
                self._process.stdin.write(json.dumps(request) + '\n')
                self._process.stdin.flush()
                deadline = time.monotonic() + (13 if action == 'shell' else 3)
                while time.monotonic() < deadline:
                    record = self._messages.get(timeout=max(.01, deadline - time.monotonic()))
                    if record.get('nonce') == nonce and record.get('ok'):
                        return record
                    raise OwnershipLost('Phone ownership receipt was rejected or changed.')
                raise OwnershipLost('Phone ownership receipt timed out.')
            except OwnershipLost:
                self.close()
                raise
            except (OSError, ValueError, queue.Empty) as exc:
                self.close()
                raise OwnershipLost('Phone ownership receipt missing; input stopped.') from exc

    def assert_owned(self):
        self._request('ping')

    def shell(self, args):
        # Preserve adb shell's existing joined-argument semantics. No host shell runs.
        record = self._request('shell', command=' '.join(str(value) for value in args))
        return subprocess.CompletedProcess(list(args), record['returncode'], record.get('stdout', ''), '')

    def _heartbeat(self):
        while not self._closed.wait(5):
            try:
                self.assert_owned()
            except OwnershipLost:
                self.close()
                return

    def close(self):
        self._closed.set()
        process = getattr(self, '_process', None)
        if process is not None:
            try:
                process.stdin.close()
            except (OSError, ValueError, AttributeError):
                pass
            # Closing stdin lets the lock owner finish any in-flight input before exit.
            # Never kill that owner merely to free its lock for another controller.
