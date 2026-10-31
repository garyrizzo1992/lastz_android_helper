import logging
import threading
import unittest
from unittest.mock import patch

from bot.observability import AxiomLogHandler, NtfyLogHandler


class LogDeliveryBoundsTests(unittest.TestCase):
    def record(self):
        return logging.LogRecord("test", logging.INFO, __file__, 1, "message", (), None)

    def handlers(self):
        # Endpoints are never used: every send is replaced by a local fixture.
        return [AxiomLogHandler("test", "not-a-token", "https://example.invalid"),
                NtfyLogHandler("not-a-topic", server="https://example.invalid")]

    def test_burst_has_one_inflight_delivery_and_no_backlog(self):
        for handler in self.handlers():
            with self.subTest(handler=type(handler).__name__):
                entered, release, finished = threading.Event(), threading.Event(), threading.Event()
                def send(record):
                    entered.set()
                    release.wait(2)
                    finished.set()
                try:
                    with patch.object(handler, "_send", side_effect=send) as deliver:
                        handler.emit(self.record())
                        self.assertTrue(entered.wait(1))
                        for _ in range(100):
                            handler.emit(self.record())
                        self.assertEqual(deliver.call_count, 1)
                        self.assertEqual(handler.dropped_records, 100)
                        handler.close()
                        handler.emit(self.record())
                        self.assertEqual(deliver.call_count, 1)
                        release.set()
                        self.assertTrue(finished.wait(1))
                finally:
                    release.set()
                    handler.close()

    def test_thread_start_failure_releases_slot_for_later_delivery(self):
        for handler in self.handlers():
            with self.subTest(handler=type(handler).__name__):
                try:
                    with patch("bot.observability.threading.Thread.start", side_effect=RuntimeError("no thread")):
                        handler.emit(self.record())
                    self.assertEqual(handler.dropped_records, 1)
                    self.assertTrue(handler._delivery_slot.acquire(blocking=False))
                    handler._delivery_slot.release()
                finally:
                    handler.close()

    def test_failure_cutoff_does_not_create_thread(self):
        for handler in self.handlers():
            try:
                handler._failure_count = handler._max_failures
                with patch("bot.observability.threading.Thread") as thread:
                    handler.emit(self.record())
                    thread.assert_not_called()
            finally:
                handler.close()

    def test_failed_network_send_releases_slot_for_next_record(self):
        class ImmediateThread:
            def __init__(self, target, args, **kwargs):
                self.target, self.args = target, args
            def start(self):
                self.target(*self.args)

        for handler in self.handlers():
            with self.subTest(handler=type(handler).__name__):
                handler.min_interval = 0
                try:
                    with patch("bot.observability.threading.Thread", ImmediateThread), patch(
                        "bot.observability.urllib.request.urlopen", side_effect=OSError("local fixture only")
                    ) as network:
                        handler.emit(self.record())
                        handler.emit(self.record())
                    self.assertEqual(network.call_count, 2)
                    self.assertEqual(handler._failure_count, 2)
                    self.assertEqual(handler.dropped_records, 0)
                    self.assertTrue(handler._delivery_slot.acquire(blocking=False))
                    handler._delivery_slot.release()
                finally:
                    handler.close()

    def test_close_before_worker_runs_prevents_late_delivery_and_releases_slot(self):
        for handler in self.handlers():
            with self.subTest(handler=type(handler).__name__):
                workers = []
                class DelayedThread:
                    def __init__(self, target, args, **kwargs):
                        self.target, self.args = target, args
                        workers.append(self)
                    def start(self):
                        pass
                try:
                    with patch("bot.observability.threading.Thread", DelayedThread), patch.object(handler, "_send") as send:
                        handler.emit(self.record())
                        self.assertEqual(len(workers), 1)
                        handler.close()
                        workers[0].target(*workers[0].args)
                        handler.emit(self.record())
                        send.assert_not_called()
                        self.assertEqual(len(workers), 1)
                    self.assertTrue(handler._delivery_slot.acquire(blocking=False))
                    handler._delivery_slot.release()
                finally:
                    handler.close()


if __name__ == "__main__":
    unittest.main()
