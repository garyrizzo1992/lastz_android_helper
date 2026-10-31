"""Ownership loss must fence subsequent Python input; no real device is used."""
import importlib.util
import io
import queue
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('phone_ownership_tested', Path(__file__).resolve().parents[3] / 'legacy' / 'python-bot' / 'bot' / 'phone_ownership.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PhoneOwnership, OwnershipLost = module.PhoneOwnership, module.OwnershipLost
NONCE = 'a' * 32


def client(records=(), ended=False):
    c = PhoneOwnership.__new__(PhoneOwnership)
    c._token = 'b' * 32
    c._lock = threading.Lock()
    c._messages = queue.Queue()
    c._closed = threading.Event()
    stream = io.StringIO()
    c._process = types.SimpleNamespace(poll=lambda: 1 if ended else None, stdin=stream)
    for record in records:
        c._messages.put(record)
    return c, stream


class OwnershipTests(unittest.TestCase):
    def call(self, c, action='ping', **values):
        with patch.object(module.uuid, 'uuid4', return_value=types.SimpleNamespace(hex=NONCE)):
            return c._request(action, **values)

    def test_matching_ack(self):
        c, stream = client([dict(nonce=NONCE, ok=True)])
        self.assertTrue(self.call(c)['ok'])
        self.assertIn('"action": "ping"', stream.getvalue())

    def test_wrong_nonce_closes_and_blocks_next_input(self):
        c, _ = client([dict(nonce='different', ok=True)])
        with self.assertRaises(OwnershipLost):
            self.call(c, 'shell', command='input tap 1 2')
        self.assertTrue(c._closed.is_set())
        with self.assertRaises(OwnershipLost):
            self.call(c, 'shell', command='input tap 3 4')

    def test_rejected_receipt_stops(self):
        c, _ = client([dict(nonce=NONCE, ok=False)])
        with self.assertRaises(OwnershipLost):
            self.call(c)
        self.assertTrue(c._closed.is_set())

    def test_dead_owner_sends_nothing(self):
        c, stream = client(ended=True)
        with self.assertRaises(OwnershipLost):
            self.call(c, 'shell', command='input tap 1 2')
        self.assertEqual(stream.getvalue(), '')

    def test_closed_owner_sends_nothing(self):
        c, stream = client()
        c._closed.set()
        with self.assertRaises(OwnershipLost):
            self.call(c)
        self.assertEqual(stream.getvalue(), '')

    def test_missing_ack_does_not_retry_shell(self):
        c, _ = client()
        with patch.object(c._messages, 'get', side_effect=queue.Empty):
            with self.assertRaises(OwnershipLost):
                self.call(c, 'shell', command='input tap 1 2')
        self.assertTrue(c._closed.is_set())

    def test_shell_returns_only_its_matching_receipt(self):
        c, _ = client([dict(nonce=NONCE, ok=True, returncode=0, stdout='done')])
        with patch.object(module.uuid, 'uuid4', return_value=types.SimpleNamespace(hex=NONCE)):
            result = c.shell(['input', 'keyevent', '4'])
        self.assertEqual((result.returncode, result.stdout), (0, 'done'))

    def test_broken_transport_fences_future_commands(self):
        c, _ = client()
        c._process.stdin.close()
        with self.assertRaises(OwnershipLost):
            self.call(c, 'shell', command='input keyevent 4')
        self.assertTrue(c._closed.is_set())


if __name__ == '__main__':
    unittest.main()
