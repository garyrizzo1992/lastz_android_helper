"""Stable workflow outcomes; legacy return values remain compatible."""
from dataclasses import dataclass
from enum import StrEnum


class Outcome(StrEnum):
    COMPLETED = "completed"
    NOTHING_TO_DO = "nothing_to_do"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(frozen=True)
class WorkflowResult:
    outcome: Outcome
    reason: str = ""

    @classmethod
    def from_legacy(cls, outcome, reason=""):
        if outcome in ("success", "completed", "collected"):
            return cls(Outcome.COMPLETED, reason)
        if outcome in ("failed", "error"):
            return cls(Outcome.FAILED, reason)
        if outcome in ("skipped", "nothing_to_do"):
            return cls(Outcome.NOTHING_TO_DO, reason)
        no_work = ("no dispatchable", "no hospital", "already sold out", "limit already reached", "no research available")
        if any(phrase in reason.lower() for phrase in no_work):
            return cls(Outcome.NOTHING_TO_DO, reason)
        return cls(Outcome.BLOCKED, reason)
