import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from status_store import ActionStatusStore, daily_period


class DailyPeriodTests(unittest.TestCase):
    def test_before_reset_belongs_to_previous_day_during_spring_dst(self):
        period, next_reset = daily_period(
            dt.datetime(2026, 3, 29, 1, 30, tzinfo=dt.timezone.utc)
        )
        self.assertEqual(period, "2026-03-28")
        self.assertEqual(next_reset.hour, 4)
        self.assertEqual(next_reset.utcoffset(), dt.timedelta(hours=2))

    def test_after_reset_belongs_to_current_day_during_spring_dst(self):
        period, next_reset = daily_period(
            dt.datetime(2026, 3, 29, 2, 30, tzinfo=dt.timezone.utc)
        )
        self.assertEqual(period, "2026-03-29")
        self.assertEqual(next_reset.date(), dt.date(2026, 3, 30))

    def test_autumn_dst_uses_malta_standard_time(self):
        period, next_reset = daily_period(
            dt.datetime(2026, 10, 25, 2, 30, tzinfo=dt.timezone.utc)
        )
        self.assertEqual(period, "2026-10-24")
        self.assertEqual(next_reset.utcoffset(), dt.timedelta(hours=1))


class ActionStatusStoreTests(unittest.TestCase):
    def test_records_and_reloads_account_action(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            store = ActionStatusStore(path, {"game1": {"label": "Farm 1"}})
            store.record("game1", "gathering", "success", "Wood march sent", resource="Wood")

            reloaded = ActionStatusStore(path)
            action = reloaded.snapshot()["accounts"]["game1"]["actions"]["gathering"]
            self.assertEqual(action["outcome"], "success")
            self.assertEqual(action["successes"], 1)
            self.assertEqual(action["details"]["resource"], "Wood")

    def test_daily_completion_survives_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            store = ActionStatusStore(path, {"game1": {}})
            store.mark_daily_complete("game1", "trucks", "Counter reached limit", used=4, total=4)

            reloaded = ActionStatusStore(path)
            self.assertTrue(reloaded.daily_complete("game1", "trucks"))
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("next_check_at", payload["accounts"]["game1"]["actions"]["trucks"])

    def test_mail_daily_completion_survives_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            store = ActionStatusStore(path, {"game1": {}})
            store.mark_daily_complete(
                "game1",
                "mail_rewards",
                "All Mail tabs checked",
                tabs=["report", "jungle", "alliance"],
            )

            reloaded = ActionStatusStore(path)
            self.assertTrue(reloaded.daily_complete("game1", "mail_rewards"))
            action = reloaded.snapshot()["accounts"]["game1"]["actions"]["mail_rewards"]
            self.assertEqual(action["details"]["tabs"], ["report", "jungle", "alliance"])
            self.assertIn("next_check_at", action)

    def test_training_full_pause_survives_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            store = ActionStatusStore(path, {"game1": {}})
            store.mark_daily_complete(
                "game1",
                "troop_training_full",
                "Military Center unit cap reached; training paused",
            )

            reloaded = ActionStatusStore(path)
            self.assertTrue(reloaded.daily_complete("game1", "troop_training_full"))
            action = reloaded.snapshot()["accounts"]["game1"]["actions"]["troop_training_full"]
            self.assertIn("next_check_at", action)


if __name__ == "__main__":
    unittest.main()
