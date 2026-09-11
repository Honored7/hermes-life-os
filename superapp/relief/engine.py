"""Ranking engine: which proven method fits THIS person, RIGHT NOW.

Scoring (preserved from the Motif engine, rewired onto the ledger):
  base 50
  - severity distance from the intervention's sweet spot  (-3 per point)
  + fast-acting bonus at severity >= 7  (+15 immediate / +10 short)
  + discreet / work-friendly at work, short when time is scarce
  + personal effectiveness from the ledger  ((avg 1-5 minus 3) * 10)
  - recency penalty  (-5 per use in the last 24h)
  + small jitter so ties rotate instead of repeating one answer

Contraindications and feasibility filter BEFORE scoring: an intervention
that doesn't fit the moment never ranks, however effective it was before.
Protocols (multi-step journeys) attach at high severity via get_protocol.
"""

from __future__ import annotations

import random
from typing import Any

from superapp.relief import interventions as library
from superapp.relief import protocols as protocol_lib
from superapp.relief.api import Recommendation, ReliefLedger, ReliefResult
from superapp.relief.interventions import Intervention


class WellnessEngine:
    """Stateless ranker. Personalization arrives via the ledger argument."""

    def recommend(
        self,
        state: str,
        severity: int = 5,
        context: dict[str, Any] | None = None,
        limit: int = 3,
        ledger: ReliefLedger | None = None,
    ) -> ReliefResult:
        from superapp.relief.ledger import InMemoryLedger

        context = context or {}
        active_protocol = protocol_lib.get_protocol(state, severity)

        candidates = library.get_by_state(state)
        candidates = [iv for iv in candidates if iv.matches_severity(severity)]
        candidates = [iv for iv in candidates if iv.is_feasible(context)]
        candidates = [
            iv for iv in candidates
            if not self._has_contraindication(iv, context)
        ]

        ledger = ledger if ledger is not None else InMemoryLedger()
        scored = [
            Recommendation(
                name=iv.name,
                score=self._compute_score(iv, state, severity, context, ledger),
                reason=self._explain_score(iv, state, severity),
                duration_seconds=iv.duration_seconds,
            )
            for iv in candidates
        ]
        scored.sort(key=lambda r: r.score, reverse=True)

        return ReliefResult(
            recommendations=scored[:limit],
            protocol=active_protocol.name if active_protocol else None,
            context={
                "state": state,
                "severity": severity,
                "context": context,
                "top": scored[0].name if scored else None,
                "protocol_active": active_protocol is not None,
            },
        )

    def _compute_score(
        self,
        iv: Intervention,
        state: str,
        severity: int,
        context: dict[str, Any],
        ledger: ReliefLedger,
    ) -> float:
        score = 50.0
        center = (iv.severity_range[0] + iv.severity_range[1]) / 2
        score -= abs(severity - center) * 3

        if severity >= 7 and iv.intensity.value == "immediate":
            score += 15
        elif severity >= 7 and iv.intensity.value == "short":
            score += 10

        if context.get("location", "home") == "work":
            if "discreet" in iv.tags or "work_friendly" in iv.tags:
                score += 10
            if iv.duration_seconds <= 180:
                score += 5

        if context.get("time_available_min", 999) <= 3 \
                and iv.duration_seconds <= 180:
            score += 10

        score += self._history_score(iv, ledger)
        score -= self._recency_penalty(iv, ledger)
        score += random.uniform(-2, 2)
        return max(score, 0.0)

    def _history_score(
        self, iv: Intervention, ledger: ReliefLedger
    ) -> float:
        """Personal effectiveness: what worked for THIS person before."""
        try:
            avg = ledger.effectiveness_for(iv.name)
        except Exception:
            return 0.0
        if avg is None:
            return 0.0
        return (avg - 3) * 10  # 1-5 scale maps to -20..+20

    def _recency_penalty(
        self, iv: Intervention, ledger: ReliefLedger
    ) -> float:
        """Rotate methods: penalize reuse within the last 24h."""
        recent_uses = getattr(ledger, "recent_uses", None)
        if not callable(recent_uses):
            return 0.0
        try:
            return recent_uses(iv.name) * 5
        except Exception:
            return 0.0

    def _has_contraindication(
        self, iv: Intervention, context: dict[str, Any]
    ) -> bool:
        active = set(context.get("conditions", []))
        tod = context.get("time_of_day", "afternoon")
        for c in iv.contraindications:
            if c in active:
                return True
            if c == "late_night" and tod == "night":
                return True
            if c == "late_evening" and tod in ("evening", "night"):
                return True
        return False

    def _explain_score(
        self, iv: Intervention, state: str, severity: int
    ) -> str:
        reasons = []
        if severity >= 7 and iv.intensity.value == "immediate":
            reasons.append("fast-acting for high intensity")
        elif iv.intensity.value == "short":
            reasons.append("quick and accessible")
        if "discreet" in iv.tags:
            reasons.append("can be done privately")
        if not reasons:
            reasons.append(f"effective for {state}")
        return f"Recommended: {', '.join(reasons)}"
