"""Relief public API: recommendation + outcome ledger contracts.

Migration plan (relief first, as agreed):
  1. Library landed verbatim: superapp/relief/{interventions,protocols}.py
     (proven methods, byte-identical to the Motif sources).
  2. Engine scoring rewired onto ReliefLedger (superapp/relief/engine.py):
     severity-match + context fit + ledger effectiveness + recency.
  3. Safety gateway extracted (superapp/relief/safety.py): crisis backstop,
     injection shield, system voice. Every LLM relief call must pass
     safety.gate() first. Full wizard (LLM loop, grounded retrieval)
     migrates with the experience layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


class ReliefNotMigratedError(RuntimeError):
    """Raised when relief is called before the proven methods migrate over."""


@dataclass
class Recommendation:
    name: str
    score: float
    reason: str
    duration_seconds: int = 0
    protocol: str | None = None


@dataclass
class ReliefResult:
    recommendations: list[Recommendation] = field(default_factory=list)
    protocol: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


class ReliefLedger(Protocol):
    """Typed outcome log: what actually helped THIS person. Replaces
    search_memory(f"intervention {name}") substring scans."""

    def log_outcome(
        self,
        *,
        name: str,
        state: str,
        severity_before: int,
        severity_after: int | None,
        effectiveness: int | None,
    ) -> None: ...

    def effectiveness_for(self, name: str) -> float | None:
        """Mean effectiveness 1-5 for an intervention, or None if unknown."""

    def recent_uses(self, name: str, hours: int = 24) -> int:
        """Uses of an intervention in the last N hours (recency rotation)."""
        return 0


def _library_present() -> bool:
    return (
        Path(__file__).resolve().parent / "interventions.py"
    ).is_file() and (
        Path(__file__).resolve().parent / "engine.py"
    ).is_file()


def relief_available() -> bool:
    """True once the Motif relief methods have migrated onto this branch."""
    return _library_present()


def recommend(
    state: str,
    severity: int = 5,
    context: dict[str, Any] | None = None,
    limit: int = 3,
    ledger: ReliefLedger | None = None,
) -> ReliefResult:
    """Rank relief for an emotional state, personalized to the user.

    Scoring: severity-match + context fit + ledger effectiveness +
    recency penalty (see superapp/relief/engine.py). Pass a ledger to
    personalize; without one, a store-backed ledger is used so outcomes
    persist, falling back to an empty in-memory ledger when storage is
    unavailable (e.g. bare test envs).
    """
    if not relief_available():
        raise ReliefNotMigratedError(
            "Relief methods not yet migrated: bring demo/wellness/"
            "{interventions,protocols,engine}.py from "
            "feature/wellness-wizard (stash: motif-wip-before-superapp) "
            "into superapp/relief/ first."
        )
    from superapp.relief.engine import WellnessEngine

    if ledger is None:
        ledger = _default_ledger()
    return WellnessEngine().recommend(
        state=state,
        severity=severity,
        context=context or {},
        limit=limit,
        ledger=ledger,
    )


def _default_ledger() -> ReliefLedger:
    """Store-backed ledger, or empty in-memory when storage is unusable."""
    try:
        from superapp.core import get_store
        from superapp.relief.ledger import StoreLedger

        return StoreLedger(get_store())
    except Exception:
        from superapp.relief.ledger import InMemoryLedger

        return InMemoryLedger()


def complete_outcome(
    ledger: ReliefLedger,
    *,
    name: str,
    state: str,
    severity_before: int,
    severity_after: int | None = None,
    effectiveness: int | None = None,
) -> None:
    """Record what happened so the NEXT recommendation is more personal."""
    ledger.log_outcome(
        name=name,
        state=state,
        severity_before=severity_before,
        severity_after=severity_after,
        effectiveness=effectiveness,
    )
