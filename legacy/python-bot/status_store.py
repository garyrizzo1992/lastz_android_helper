"""Persistent action status for the LastZ bot."""

from __future__ import annotations

import copy
import datetime as dt
import json
import math
import os
import threading
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
from workflow_result import WorkflowResult, Outcome


SCHEMA_VERSION = 1


def daily_period(
    now: dt.datetime | None = None,
    *,
    timezone_name: str = "Europe/Malta",
    reset_hour: int = 4,
) -> tuple[str, dt.datetime]:
    """Return the active game-day key and the next timezone-aware reset."""
    timezone = ZoneInfo(timezone_name)
    local_now = now.astimezone(timezone) if now else dt.datetime.now(timezone)
    reset_today = local_now.replace(
        hour=int(reset_hour), minute=0, second=0, microsecond=0
    )
    if local_now < reset_today:
        period_date = (local_now - dt.timedelta(days=1)).date()
        next_reset = reset_today
    else:
        period_date = local_now.date()
        next_reset = (local_now + dt.timedelta(days=1)).replace(
            hour=int(reset_hour), minute=0, second=0, microsecond=0
        )
    return period_date.isoformat(), next_reset


class ActionStatusStore:
    """Thread-safe, atomic JSON state shared by the bot and status publisher."""

    def __init__(
        self,
        path: str | os.PathLike[str],
        accounts: dict[str, dict[str, Any]] | None = None,
        *,
        timezone_name: str = "Europe/Malta",
        reset_hour: int = 4,
    ) -> None:
        self.path = Path(path)
        self.timezone_name = timezone_name
        self.reset_hour = int(reset_hour)
        self._timezone = ZoneInfo(timezone_name)
        self._lock = threading.RLock()
        self._state = self._load()
        for account, settings in (accounts or {}).items():
            entry = self._state["accounts"].setdefault(account, {"actions": {}})
            entry.setdefault("actions", {})
            entry["label"] = str(settings.get("label", account))
        self._write_locked()

    def _now(self) -> dt.datetime:
        return dt.datetime.now(self._timezone)

    def _base_state(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "generated_at": None,
            "timezone": self.timezone_name,
            "reset_hour": self.reset_hour,
            "next_reset_at": None,
            "bot": {"status": "starting"},
            "accounts": {},
        }

    def _load(self) -> dict[str, Any]:
        state = self._base_state()
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                state.update(loaded)
                if not isinstance(state.get("accounts"), dict):
                    state["accounts"] = {}
                if not isinstance(state.get("bot"), dict):
                    state["bot"] = {"status": "starting"}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        state["schema_version"] = SCHEMA_VERSION
        state["timezone"] = self.timezone_name
        state["reset_hour"] = self.reset_hour
        return state

    def _write_locked(self) -> None:
        now = self._now()
        _, next_reset = daily_period(
            now, timezone_name=self.timezone_name, reset_hour=self.reset_hour
        )
        self._state["generated_at"] = now.isoformat(timespec="seconds")
        self._state["next_reset_at"] = next_reset.isoformat(timespec="seconds")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(self._state, handle, indent=2, sort_keys=True, ensure_ascii=True)
            handle.write("\n")
        os.replace(temporary, self.path)

    def set_bot(self, status: str, message: str = "", **details: Any) -> None:
        with self._lock:
            now = self._now().isoformat(timespec="seconds")
            bot = self._state.setdefault("bot", {})
            bot.update({"status": status, "updated_at": now})
            if message:
                bot["message"] = message
            if details:
                bot["details"] = details
            self._write_locked()

    def record(
        self,
        account: str,
        action: str,
        outcome: str,
        message: str = "",
        **details: Any,
    ) -> None:
        """Record the latest outcome and retain success/failure totals."""
        with self._lock:
            now = self._now().isoformat(timespec="seconds")
            account_state = self._state["accounts"].setdefault(
                account, {"label": account, "actions": {}}
            )
            action_state = account_state.setdefault("actions", {}).setdefault(
                action, {"attempts": 0, "successes": 0, "failures": 0}
            )
            action_state["attempts"] = int(action_state.get("attempts", 0)) + 1
            action_state["outcome"] = outcome
            action_state["last_attempt_at"] = now
            action_state["message"] = message
            result = WorkflowResult.from_legacy(outcome, message)
            action_state["result"] = result.outcome.value
            action_state["reason"] = result.reason
            action_state["consecutive_failures"] = (
                int(action_state.get("consecutive_failures", 0)) + 1
                if result.outcome == Outcome.FAILED else 0
            )
            if details:
                action_state["details"] = details
            elif "details" in action_state:
                action_state.pop("details")

            if outcome == "success":
                action_state["successes"] = int(action_state.get("successes", 0)) + 1
                action_state["last_success_at"] = now
            elif outcome == "failed":
                action_state["failures"] = int(action_state.get("failures", 0)) + 1
                action_state["last_failure_at"] = now

            account_state["updated_at"] = now
            self._write_locked()

    def mark_cycle(self, account: str, outcome: str, message: str = "", **details: Any) -> None:
        self.record(account, "cycle", outcome, message, **details)

    def mark_daily_complete(
        self,
        account: str,
        action: str,
        message: str = "",
        **details: Any,
    ) -> None:
        with self._lock:
            period, next_reset = daily_period(
                self._now(),
                timezone_name=self.timezone_name,
                reset_hour=self.reset_hour,
            )
            self.record(account, action, "success", message, **details)
            action_state = self._state["accounts"][account]["actions"][action]
            action_state["daily_period"] = period
            action_state["daily_completed_at"] = self._now().isoformat(timespec="seconds")
            action_state["next_check_at"] = next_reset.isoformat(timespec="seconds")
            self._write_locked()

    def daily_complete(self, account: str, action: str) -> bool:
        with self._lock:
            period, _ = daily_period(
                self._now(),
                timezone_name=self.timezone_name,
                reset_hour=self.reset_hour,
            )
            action_state = (
                self._state.get("accounts", {})
                .get(account, {})
                .get("actions", {})
                .get(action, {})
            )
            return action_state.get("daily_period") == period

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._state)

    def schedule(self, name: str, next_check: float) -> None:
        with self._lock:
            self._state.setdefault("schedules", {})[name] = float(next_check)
            account = name.rsplit("_", 1)[-1]
            action = name[:-(len(account) + 1)]
            if account in self._state["accounts"]:
                entry = self._state["accounts"][account].setdefault("actions", {}).setdefault(action, {})
                entry["next_check_at"] = dt.datetime.fromtimestamp(next_check, self._timezone).isoformat(timespec="seconds")
            self._write_locked()

    def scheduled_at(self, name: str) -> float | None:
        with self._lock:
            value = self._state.get("schedules", {}).get(name)
            try:
                number = float(value)
                return number if math.isfinite(number) and number > 0 else None
            except (TypeError, ValueError):
                return None

    def account_summary(self, account: str) -> dict[str, Any]:
        with self._lock:
            actions = self._state["accounts"].get(account, {}).get("actions", {})
            return {
                name: {key: state.get(key) for key in (
                    "result", "reason", "last_success_at", "consecutive_failures", "next_check_at"
                )}
                for name, state in actions.items() if name != "cycle"
            }
