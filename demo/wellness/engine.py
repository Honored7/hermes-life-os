"""
Hermes Life OS — Wellness Recommendation Engine
=================================================
Matches emotional states to interventions using severity, context,
user history (from demo/storage.py), and recency.
"""

from __future__ import annotations

import os
import sys
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from storage import search_memory, write_memory

from wellness.interventions import Intervention, INTERVENTIONS, get_by_state
from wellness.protocols import PROTOCOLS, get_protocol, Protocol


@dataclass
class Recommendation:
    intervention: Intervention
    score: float
    reason: str


@dataclass
class EngineResult:
    recommendations: list[Recommendation]
    protocol: Optional[Protocol] = None
    wizard_context: dict = field(default_factory=dict)


class WellnessEngine:
    """Recommendation engine using Hermes memory for personalization."""

    def recommend(
        self, state: str, severity: int = 5,
        context: Optional[dict] = None, limit: int = 3,
    ) -> EngineResult:
        context = context or {}
        protocol = get_protocol(state, severity)
        candidates = get_by_state(state)
        candidates = [iv for iv in candidates if iv.matches_severity(severity)]
        candidates = [iv for iv in candidates if iv.is_feasible(context)]
        candidates = [iv for iv in candidates if not self._has_contraindication(iv, context)]

        scored = []
        for iv in candidates:
            score = self._compute_score(iv, state, severity, context)
            reason = self._explain_score(iv, score, state, severity)
            scored.append(Recommendation(intervention=iv, score=score, reason=reason))

        scored.sort(key=lambda r: r.score, reverse=True)

        return EngineResult(
            recommendations=scored[:limit],
            protocol=protocol,
            wizard_context={
                "state": state, "severity": severity, "context": context,
                "top": scored[0].intervention.name if scored else None,
                "protocol_active": protocol is not None,
            },
        )

    def _compute_score(self, iv, state, severity, context):
        score = 50.0
        range_center = (iv.severity_range[0] + iv.severity_range[1]) / 2
        score -= abs(severity - range_center) * 3

        if severity >= 7 and iv.intensity.value == "immediate":
            score += 15
        elif severity >= 7 and iv.intensity.value == "short":
            score += 10

        location = context.get("location", "home")
        if location == "work":
            if "discreet" in iv.tags or "work_friendly" in iv.tags:
                score += 10
            if iv.duration_seconds <= 180:
                score += 5

        time_available = context.get("time_available_min", 999)
        if time_available <= 3 and iv.duration_seconds <= 180:
            score += 10

        score += self._history_score(iv)
        score -= self._recency_penalty(iv)
        score += random.uniform(-2, 2)
        return max(score, 0)

    def _history_score(self, iv: Intervention) -> float:
        """Score based on past effectiveness from Hermes memory."""
        try:
            results = search_memory(f"intervention {iv.name}", limit=10)
            if not results:
                return 0
            ratings = [r.get("effectiveness") for r in results if r.get("effectiveness")]
            if not ratings:
                return 0
            avg = sum(ratings) / len(ratings)
            return (avg - 3) * 10  # Map 1-5 to -20..+20
        except Exception:
            return 0

    def _recency_penalty(self, iv: Intervention) -> float:
        """Penalize recently used interventions."""
        try:
            results = search_memory(f"intervention {iv.name}", limit=3)
            if not results:
                return 0
            now = datetime.utcnow()
            recent = 0
            for r in results:
                ts = r.get("timestamp", "")
                if ts:
                    try:
                        t = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                        if now - t < timedelta(hours=24):
                            recent += 1
                    except Exception:
                        pass
            return recent * 5
        except Exception:
            return 0

    def _has_contraindication(self, iv, context):
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

    def _explain_score(self, iv, score, state, severity):
        reasons = []
        if severity >= 7 and iv.intensity.value == "immediate":
            reasons.append("fast-acting for high intensity")
        elif iv.intensity.value == "short":
            reasons.append("quick and accessible")
        if "discreet" in iv.tags:
            reasons.append("can be done privately")
        if not reasons:
            reasons.append(f"effective for {state}")
        return f"Recommended: {', '.join(reasons)} (score: {score:.0f})"
