"""
The Wizard — LLM-powered orchestrator for the wellness intervention experience.

v2: Now with full LLM integration. When an LLM is available (Ollama, OpenAI,
or Anthropic), every response is personalized to the user's words, history,
and patterns. When no LLM is available, falls back to built-in templates.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from hermes.wellness.engine import WellnessEngine, EngineResult
from hermes.wellness.interventions import INTERVENTIONS, Intervention
from hermes.wellness.protocols import Protocol
from hermes.wellness.llm_client import LLMClient
from hermes.wellness.prompts import WIZARD_SYSTEM, PromptBuilder


class Wizard:
    """
    The Hermes Wellness Wizard — v2 with LLM integration.

    Usage:
        # Auto-detect LLM (tries Ollama → OpenAI → Anthropic → template fallback)
        wizard = Wizard()

        # Force a specific provider
        wizard = Wizard(llm_provider="ollama", llm_model="llama3.2")
        wizard = Wizard(llm_provider="openai", llm_api_key="sk-...")

        # Respond to a mood
        response = wizard.respond_to_state(
            state="stressed",
            severity=7,
            user_message="I can't stop thinking about tomorrow's presentation",
        )
        print(response["wizard_message"])
        # → "Hey. I hear you — the presentation tomorrow has your mind spinning..."
    """

    def __init__(
        self,
        memory_store=None,
        llm_provider: str = "auto",
        llm_model: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        llm_base_url: Optional[str] = None,
        pattern_detector=None,
    ):
        self.memory = memory_store
        self.patterns = pattern_detector
        self.engine = WellnessEngine(memory_store)
        self.prompts = PromptBuilder()

        # Initialize LLM client
        self.llm = LLMClient(
            provider=llm_provider,
            model=llm_model,
            api_key=llm_api_key,
            base_url=llm_base_url,
        )

    # ─── Core Response ────────────────────────────────────────────────

    def respond_to_state(
        self,
        state: str,
        severity: int = 5,
        user_message: str = "",
        context: Optional[dict] = None,
    ) -> dict:
        """Generate a wizard response for a logged emotional state."""
        context = context or {}
        context.setdefault("time_of_day", self._get_time_of_day())

        # Get engine recommendations
        result: EngineResult = self.engine.recommend(
            state=state, severity=severity, context=context,
        )

        if result.protocol:
            return self._respond_with_protocol(result, state, severity, user_message, context)
        elif result.recommendations:
            return self._respond_with_intervention(result, state, severity, user_message, context)
        else:
            return self._respond_fallback(state, severity, user_message)

    def _respond_with_intervention(
        self, result, state, severity, user_message, context,
    ) -> dict:
        top = result.recommendations[0]
        iv = top.intervention

        # Try LLM first
        wizard_message = self._llm_mood_response(
            state=state,
            severity=severity,
            user_message=user_message,
            intervention=iv,
            context=context,
            alternatives=[r.intervention.name for r in result.recommendations[1:]],
        )

        # Fallback to template
        if not wizard_message:
            wizard_message = iv.wizard_intro

        return {
            "wizard_message": wizard_message,
            "llm_used": self.llm.provider != "none",
            "intervention": {
                "id": iv.id,
                "name": iv.name,
                "family": iv.family.value,
                "duration_seconds": iv.duration_seconds,
                "format": iv.format.value,
                "steps": list(iv.steps),
                "wizard_intro": iv.wizard_intro,
                "wizard_outro": iv.wizard_outro,
            },
            "protocol": None,
            "session_config": self._build_session_config(iv),
            "alternatives": [
                {"id": r.intervention.id, "name": r.intervention.name, "reason": r.reason}
                for r in result.recommendations[1:]
            ],
        }

    def _respond_with_protocol(
        self, result, state, severity, user_message, context,
    ) -> dict:
        protocol = result.protocol
        first_step = protocol.steps[0]
        first_iv = INTERVENTIONS.get(first_step.intervention_id) if first_step.intervention_id else None

        # Try LLM
        wizard_message = self._llm_mood_response(
            state=state,
            severity=severity,
            user_message=user_message,
            intervention=first_iv,
            context=context,
            protocol_name=protocol.name,
            protocol_steps=[
                INTERVENTIONS[s.intervention_id].name if s.intervention_id else "Check-in"
                for s in protocol.steps
            ],
        )

        if not wizard_message:
            wizard_message = first_step.wizard_message

        return {
            "wizard_message": wizard_message,
            "llm_used": self.llm.provider != "none",
            "intervention": {
                "id": first_iv.id,
                "name": first_iv.name,
                "family": first_iv.family.value,
                "duration_seconds": first_iv.duration_seconds,
                "format": first_iv.format.value,
                "steps": list(first_iv.steps),
            } if first_iv else None,
            "protocol": {
                "id": protocol.id,
                "name": protocol.name,
                "total_steps": len(protocol.steps),
                "current_step": 0,
                "steps": [
                    {
                        "step_number": i,
                        "intervention_id": s.intervention_id,
                        "intervention_name": INTERVENTIONS[s.intervention_id].name if s.intervention_id else "Check-in",
                        "wizard_message": s.wizard_message,
                        "is_check_in": s.is_check_in,
                    }
                    for i, s in enumerate(protocol.steps)
                ],
            },
            "session_config": self._build_session_config(first_iv) if first_iv else None,
            "alternatives": [],
        }

    def _respond_fallback(self, state, severity, user_message):
        return {
            "wizard_message": (
                f"I hear you. {state.capitalize()} at a {severity}/10 is real, "
                f"and I don't want to throw a generic exercise at you. "
                f"Sometimes the most useful thing is just to be heard. "
                f"I'm here. You don't have to fix anything right now."
            ),
            "llm_used": False,
            "intervention": None,
            "protocol": None,
            "session_config": None,
            "alternatives": [],
        }

    # ─── Free-Form Chat ───────────────────────────────────────────────

    def chat(self, user_message: str, context: Optional[dict] = None) -> dict:
        """
        Free-form conversation with the wizard.
        The user can say anything — the wizard responds in character.
        """
        context = context or {}
        history = self._get_history_summary()

        prompt = self.prompts.build_chat_response(
            user_message=user_message,
            history_summary=history,
        )

        wizard_message = self.llm.generate(system=WIZARD_SYSTEM, prompt=prompt)

        if not wizard_message:
            wizard_message = (
                "I'm here. Tell me more about what's going on. "
                "Or if you just need to vent — I'm listening. No judgment, no fixes unless you want them."
            )

        return {
            "wizard_message": wizard_message,
            "llm_used": self.llm.provider != "none",
        }

    # ─── Celebration ──────────────────────────────────────────────────

    def celebrate_win(self, win_description: str, context: Optional[dict] = None) -> dict:
        iv = INTERVENTIONS[23]
        history = self._get_history_summary()

        prompt = self.prompts.build_celebration(
            win_description=win_description,
            history_summary=history,
        )

        wizard_message = self.llm.generate(system=WIZARD_SYSTEM, prompt=prompt)
        if not wizard_message:
            wizard_message = iv.wizard_intro

        if self.memory:
            self.memory.store({
                "type": "win_celebration",
                "description": win_description,
                "timestamp": datetime.now().isoformat(),
            })

        return {
            "wizard_message": wizard_message,
            "llm_used": self.llm.provider != "none",
            "intervention": {"id": iv.id, "name": iv.name, "steps": list(iv.steps)},
        }

    # ─── Preparation ──────────────────────────────────────────────────

    def prepare_for_stressor(self, stressor_description: str, context: Optional[dict] = None) -> dict:
        iv = INTERVENTIONS[24]
        history = self._get_history_summary()

        prompt = self.prompts.build_preparation(
            stressor=stressor_description,
            history_summary=history,
        )

        wizard_message = self.llm.generate(system=WIZARD_SYSTEM, prompt=prompt)
        if not wizard_message:
            wizard_message = iv.wizard_intro

        return {
            "wizard_message": wizard_message,
            "llm_used": self.llm.provider != "none",
            "intervention": {"id": iv.id, "name": iv.name, "steps": list(iv.steps)},
        }

    # ─── Dream Response ───────────────────────────────────────────────

    def respond_to_dream(self, dream_description: str, dream_tone: str = "neutral") -> dict:
        prompt = self.prompts.build_dream_response(
            dream_description=dream_description,
            dream_tone=dream_tone,
        )

        wizard_message = self.llm.generate(system=WIZARD_SYSTEM, prompt=prompt)

        if not wizard_message:
            # Template fallbacks per tone
            fallbacks = {
                "nightmare": (
                    "That sounds unsettling. Nightmares are your brain processing stress — "
                    "they're not predictions. Let's ground you. "
                    "5 things you can see right now. Name them. You're safe. You're here."
                ),
                "positive": (
                    "A good dream! Hold onto that feeling. "
                    "Want to write it down before it fades? Dreams like that are gifts."
                ),
                "neutral": (
                    "Interesting dream. What feeling stuck with you? "
                    "Sometimes the emotion matters more than the story."
                ),
            }
            wizard_message = fallbacks.get(dream_tone, fallbacks["neutral"])

        suggested = {
            "nightmare": [6, 8],
            "positive": [23],
            "negative": [8],
            "neutral": [8],
        }

        return {
            "wizard_message": wizard_message,
            "llm_used": self.llm.provider != "none",
            "suggested_interventions": suggested.get(dream_tone, [8]),
        }

    # ─── Post-Intervention Check-in ───────────────────────────────────

    def complete_intervention(
        self,
        intervention_id: int,
        state: str,
        severity_before: int,
        severity_after: Optional[int] = None,
        effectiveness_rating: Optional[int] = None,
        notes: str = "",
    ) -> dict:
        log_entry = self.engine.log_intervention(
            intervention_id=intervention_id,
            state=state,
            severity_before=severity_before,
            severity_after=severity_after,
            effectiveness_rating=effectiveness_rating,
            notes=notes,
        )

        iv = INTERVENTIONS.get(intervention_id)
        if not iv:
            return {"wizard_message": "Thanks for checking in.", "llm_used": False}

        # Try LLM
        prompt = self.prompts.build_check_in(
            intervention_name=iv.name,
            state=state,
            severity_before=severity_before,
            severity_after=severity_after,
            effectiveness_rating=effectiveness_rating,
        )

        wizard_message = self.llm.generate(system=WIZARD_SYSTEM, prompt=prompt)

        if not wizard_message:
            # Template fallback
            improvement = ""
            if severity_after is not None:
                diff = severity_before - severity_after
                if diff > 0:
                    improvement = f" You went from a {severity_before} to a {severity_after}. That's a real shift."
                elif diff == 0:
                    improvement = " The number didn't change, and that's okay. Sometimes just pausing is the win."

            wizard_message = f"{iv.wizard_outro}{improvement}"

        return {
            "wizard_message": wizard_message,
            "llm_used": self.llm.provider != "none",
            "log_entry": log_entry,
        }

    # ─── Protocol Navigation ──────────────────────────────────────────

    def advance_protocol(self, protocol_id, current_step, user_feedback=None):
        from hermes.wellness.protocols import PROTOCOLS

        protocol = PROTOCOLS.get(protocol_id)
        if not protocol:
            return {"error": f"Unknown protocol: {protocol_id}"}

        next_idx = current_step + 1
        if next_idx >= len(protocol.steps):
            # Protocol complete — try LLM for the closing message
            prompt = (
                f"The user just completed the '{protocol.name}' protocol "
                f"({len(protocol.steps)} steps). They started feeling {protocol.trigger_state} "
                f"at severity {protocol.trigger_severity_min}+. "
                "Celebrate their effort warmly. Ask how they're feeling now. "
                "Remind them they chose to do something for themselves. Keep it under 80 words."
            )
            wizard_message = self.llm.generate(system=WIZARD_SYSTEM, prompt=prompt)
            if not wizard_message:
                wizard_message = (
                    f"You completed the {protocol.name}. "
                    f"That took real effort. How are you feeling now?"
                )
            return {
                "wizard_message": wizard_message,
                "llm_used": self.llm.provider != "none",
                "protocol_complete": True,
                "next_step": None,
            }

        next_step = protocol.steps[next_idx]
        iv = INTERVENTIONS.get(next_step.intervention_id) if next_step.intervention_id else None

        # Try LLM for the transition message
        wizard_message = None
        if iv:
            prompt = (
                f"The user is doing the '{protocol.name}' protocol. "
                f"They just finished step {current_step + 1}. "
                f"Now guide them into the next step: {iv.name}. "
                f"Context: {next_step.wizard_message}\n"
                f"Keep the transition warm and brief. Under 60 words."
            )
            wizard_message = self.llm.generate(system=WIZARD_SYSTEM, prompt=prompt)

        if not wizard_message:
            wizard_message = next_step.wizard_message

        return {
            "wizard_message": wizard_message,
            "llm_used": self.llm.provider != "none",
            "protocol_complete": False,
            "next_step": {
                "step_number": next_idx,
                "intervention_id": next_step.intervention_id,
                "intervention_name": iv.name if iv else "Check-in",
                "is_check_in": next_step.is_check_in,
                "steps": list(iv.steps) if iv else [],
                "session_config": self._build_session_config(iv) if iv else None,
            },
        }

    # ─── LLM Prompt Helpers ───────────────────────────────────────────

    def _llm_mood_response(
        self, state, severity, user_message, intervention, context,
        alternatives=None, protocol_name=None, protocol_steps=None,
    ) -> Optional[str]:
        """Generate an LLM-powered mood response."""
        if self.llm.provider == "none":
            return None

        history = self._get_history_summary(state)

        prompt = self.prompts.build_mood_response(
            state=state,
            severity=severity,
            user_message=user_message,
            intervention_name=intervention.name if intervention else "General support",
            intervention_description=intervention.description if intervention else "",
            intervention_steps=list(intervention.steps) if intervention else [],
            intervention_duration=intervention.duration_seconds if intervention else 0,
            context=context,
            history_summary=history,
            alternatives=alternatives,
            protocol_name=protocol_name,
            protocol_steps=protocol_steps,
        )

        return self.llm.generate(system=WIZARD_SYSTEM, prompt=prompt)

    # ─── History & Context ────────────────────────────────────────────

    def _get_history_summary(self, state: str = None) -> str:
        if not self.memory:
            return ""
        try:
            parts = []
            if state:
                entries = self.memory.search(f"mood:{state}", limit=5)
                if entries:
                    parts.append(f"Logged '{state}' {len(entries)} time(s) recently.")

            interventions = self.memory.search("type:intervention_log", limit=5)
            if interventions:
                names = [e.get("intervention_name", "?") for e in interventions]
                parts.append(f"Recent interventions tried: {', '.join(names)}.")

            wins = self.memory.search("type:win_celebration", limit=3)
            if wins:
                parts.append(f"Recent wins: {len(wins)} celebrated.")

            return " ".join(parts) if parts else ""
        except Exception:
            return ""

    def _build_session_config(self, iv: Optional[Intervention]) -> Optional[dict]:
        if not iv:
            return None
        config = {
            "intervention_id": iv.id,
            "name": iv.name,
            "format": iv.format.value,
            "duration_seconds": iv.duration_seconds,
            "steps": list(iv.steps),
        }
        if iv.family.value == "breathwork":
            if iv.id == 1:
                config["breathing_pattern"] = {"inhale": 4, "hold_in": 7, "exhale": 8, "hold_out": 0, "cycles": 4}
            elif iv.id == 2:
                config["breathing_pattern"] = {"inhale": 4, "hold_in": 4, "exhale": 4, "hold_out": 4, "cycles": 8}
        return config

    def _get_time_of_day(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        return "night"

    # ─── Status ───────────────────────────────────────────────────────

    def status(self) -> dict:
        return {
            "llm": self.llm.status(),
            "interventions": len(INTERVENTIONS),
            "engine": "active",
        }
