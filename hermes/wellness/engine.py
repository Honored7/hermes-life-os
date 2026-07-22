"""
Wellness Engine — Matches emotional states to the right interventions.

The engine considers:
1. Emotional state match
2. Severity appropriateness
3. Context feasibility (location, time, resources)
4. Contraindications
5. User history (what worked before)
6. Recency (don't suggest the same thing 3x in a row)
7. Protocol eligibility (should we chain interventions?)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from hermes.wellness.interventions import (
    Intervention,
    INTERVENTIONS,
    get_by_state,
)
from hermes.wellness.protocols import PROTOCOLS, get_protocol, Protocol


@dataclass
class Recommendation:
    """A scored intervention recommendation."""
    intervention: Intervention
    score: float
    reason: str  # Why this was recommended


@dataclass
class EngineResult:
    """The full result of an engine query."""
    recommendations: list[Recommendation]
    protocol: Optional[Protocol] = None
    wizard_context: dict = field(default_factory=dict)


class WellnessEngine:
    """
    Core recommendation engine for the wellness wizard.

    Usage:
        engine = WellnessEngine(memory_store)
        result = engine.recommend(
            state="stressed",
            severity=7,
            context={"location": "work", "time_available_min": 5},
        )
        # result.recommendations[0].intervention → Box Breathing
        # result.protocol → None (or a chained protocol for high severity)
    """

    def __init__(self, memory_store=None):
        """
        Args:
            memory_store: Hermes MemoryStore instance for reading user history.
                          If None, engine works without personalization.
        """
        self.memory = memory_store

    def recommend(
        self,
        state: str,
        severity: int = 5,
        context: Optional[dict] = None,
        limit: int = 3,
    ) -> EngineResult:
        """
        Recommend interventions for a given emotional state.

        Args:
            state: Emotional state (e.g., "stressed", "angry", "sad")
            severity: 1-10 intensity scale
            context: User context dict with keys like:
                - location: "work", "home", "outside"
                - time_available_min: int
                - can_go_outside: bool
                - has_quiet_space: bool
                - has_water: bool
                - has_pen_paper: bool
                - time_of_day: "morning", "afternoon", "evening", "night"
            limit: Max number of recommendations to return

        Returns:
            EngineResult with ranked recommendations and optional protocol
        """
        context = context or {}

        # Step 1: Check if a protocol applies (for high-severity states)
        protocol = get_protocol(state, severity)

        # Step 2: Get candidate interventions
        candidates = get_by_state(state)

        # Step 3: Filter by severity
        candidates = [iv for iv in candidates if iv.matches_severity(severity)]

        # Step 4: Filter by feasibility
        candidates = [iv for iv in candidates if iv.is_feasible(context)]

        # Step 5: Filter by contraindications
        candidates = [iv for iv in candidates if not self._has_contraindication(iv, context)]

        # Step 6: Score each candidate
        scored = []
        for iv in candidates:
            score = self._compute_score(iv, state, severity, context)
            reason = self._explain_score(iv, score, state, severity)
            scored.append(Recommendation(intervention=iv, score=score, reason=reason))

        # Step 7: Sort by score, take top N
        scored.sort(key=lambda r: r.score, reverse=True)
        recommendations = scored[:limit]

        # Step 8: Build wizard context
        wizard_context = {
            "state": state,
            "severity": severity,
            "context": context,
            "top_recommendation": recommendations[0].intervention.name if recommendations else None,
            "protocol_active": protocol is not None,
            "user_history_summary": self._get_history_summary(state),
        }

        return EngineResult(
            recommendations=recommendations,
            protocol=protocol,
            wizard_context=wizard_context,
        )

    def _compute_score(
        self,
        iv: Intervention,
        state: str,
        severity: int,
        context: dict,
    ) -> float:
        """
        Score an intervention for the current situation.
        Higher score = better recommendation.
        """
        score = 50.0  # Base score

        # Severity alignment: prefer interventions whose range center is close to severity
        range_center = (iv.severity_range[0] + iv.severity_range[1]) / 2
        severity_distance = abs(severity - range_center)
        score -= severity_distance * 3  # Penalize mismatch

        # Immediate interventions get a bonus for high severity
        if severity >= 7 and iv.intensity.value == "immediate":
            score += 15
        elif severity >= 7 and iv.intensity.value == "short":
            score += 10

        # Context bonuses
        location = context.get("location", "home")
        time_available = context.get("time_available_min", 999)

        if location == "work":
            if "discreet" in iv.tags or "work_friendly" in iv.tags:
                score += 10
            if iv.duration_seconds <= 180:  # ≤ 3 min at work
                score += 5

        if time_available <= 3 and iv.duration_seconds <= 180:
            score += 10  # Quick interventions when time is short

        # User history: boost interventions that worked before
        history_score = self._history_score(iv, state)
        score += history_score

        # Recency penalty: don't suggest the same thing repeatedly
        recency_penalty = self._recency_penalty(iv)
        score -= recency_penalty

        # Small random factor for variety
        score += random.uniform(-2, 2)

        return max(score, 0)

    def _history_score(self, iv: Intervention, state: str) -> float:
        """
        Score based on user's past experience with this intervention.
        Returns a bonus/penalty from -20 to +20.
        """
        if not self.memory:
            return 0

        try:
            # Query memory for past intervention logs
            history = self.memory.search(
                f"intervention:{iv.name}",
                limit=10,
            )
            if not history:
                return 0  # No history, neutral

            # Calculate average effectiveness
            ratings = []
            for entry in history:
                rating = entry.get("effectiveness_rating")
                if rating is not None:
                    ratings.append(rating)

            if not ratings:
                return 0

            avg_rating = sum(ratings) / len(ratings)
            # Map 1-5 rating to -20 to +20 bonus
            return (avg_rating - 3) * 10

        except Exception:
            return 0  # Graceful fallback if memory query fails

    def _recency_penalty(self, iv: Intervention) -> float:
        """
        Penalize interventions used recently to encourage variety.
        Returns a penalty from 0 to 15.
        """
        if not self.memory:
            return 0

        try:
            recent = self.memory.search(
                f"intervention:{iv.name}",
                limit=3,
            )
            if not recent:
                return 0

            # Check if used in the last 24 hours
            now = datetime.now()
            recent_uses = 0
            for entry in recent:
                timestamp = entry.get("timestamp")
                if timestamp:
                    entry_time = datetime.fromisoformat(timestamp)
                    if now - entry_time < timedelta(hours=24):
                        recent_uses += 1

            return recent_uses * 5  # 5 points per recent use

        except Exception:
            return 0

    def _has_contraindication(self, iv: Intervention, context: dict) -> bool:
        """Check if any contraindication applies given the context."""
        active_conditions = set(context.get("conditions", []))
        time_of_day = context.get("time_of_day", "afternoon")

        for contra in iv.contraindications:
            if contra in active_conditions:
                return True
            # Time-based contraindications
            if contra == "late_night" and time_of_day == "night":
                return True
            if contra == "late_evening" and time_of_day in ("evening", "night"):
                return True

        return False

    def _explain_score(
        self,
        iv: Intervention,
        score: float,
        state: str,
        severity: int,
    ) -> str:
        """Generate a human-readable reason for the recommendation."""
        reasons = []

        if severity >= 7 and iv.intensity.value == "immediate":
            reasons.append("fast-acting for high intensity")
        elif iv.intensity.value == "short":
            reasons.append("quick and accessible")

        if "discreet" in iv.tags:
            reasons.append("can be done privately")
        if "work_friendly" in iv.tags:
            reasons.append("works at your desk")

        if not reasons:
            reasons.append(f"effective for {state}")

        return f"Recommended: {', '.join(reasons)} (score: {score:.0f})"

    def _get_history_summary(self, state: str) -> str:
        """Get a brief summary of the user's history with this state."""
        if not self.memory:
            return "No history available."

        try:
            entries = self.memory.search(f"mood:{state}", limit=5)
            if not entries:
                return f"First time logging '{state}'."

            count = len(entries)
            return f"Logged '{state}' {count} time(s) recently."

        except Exception:
            return "History unavailable."

    def log_intervention(
        self,
        intervention_id: int,
        state: str,
        severity_before: int,
        severity_after: Optional[int] = None,
        effectiveness_rating: Optional[int] = None,
        notes: str = "",
    ) -> dict:
        """
        Log a completed intervention for the feedback loop.

        Args:
            intervention_id: Which intervention was done
            state: The emotional state it was for
            severity_before: Severity before the intervention (1-10)
            severity_after: Severity after (1-10), if known
            effectiveness_rating: User's rating (1-5)
            notes: Any user notes

        Returns:
            The logged entry
        """
        iv = INTERVENTIONS.get(intervention_id)
        if not iv:
            raise ValueError(f"Unknown intervention ID: {intervention_id}")

        entry = {
            "type": "intervention_log",
            "intervention_id": intervention_id,
            "intervention_name": iv.name,
            "family": iv.family.value,
            "state": state,
            "severity_before": severity_before,
            "severity_after": severity_after,
            "effectiveness_rating": effectiveness_rating,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }

        # Calculate improvement if we have both scores
        if severity_after is not None:
            entry["improvement"] = severity_before - severity_after

        if self.memory:
            self.memory.store(entry)

        return entry
