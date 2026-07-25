"""
Hermes Life OS — The Wellness Wizard
======================================
LLM-powered companion that responds to emotional states with
personalized interventions, celebrates wins, and guides protocols.

Uses the EXISTING Hermes Life OS infrastructure:
  - demo/llm_providers.py  → LLM client (ollama/openai/anthropic/openrouter)
  - demo/storage.py        → Memory (write_memory, search_memory)
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Optional

# Ensure demo/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from llm_providers import resolve_provider, get_client, default_model_for
from storage import write_memory, search_memory

from wellness.engine import WellnessEngine, EngineResult
from wellness.interventions import INTERVENTIONS, Intervention
from wellness.prompts import WIZARD_SYSTEM, PromptBuilder


class Wizard:
    """
    The Hermes Wellness Wizard.

    Uses the same LLM infrastructure as the rest of Life OS.
    No separate client. No duplicate config. One source of truth.

    Usage:
        wizard = Wizard()
        response = wizard.respond_to_state("stressed", severity=7,
                                           user_message="deadline tomorrow")
        print(response["wizard_message"])
    """

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        # Use the EXISTING Hermes LLM infrastructure
        self.provider_name = resolve_provider(provider)
        self.client = get_client(self.provider_name)
        self.model = model or os.environ.get(
            "LIFE_OS_MODEL",
            default_model_for(self.provider_name),
        )
        self.engine = WellnessEngine()
        self.prompts = PromptBuilder()
    def chat_stream(self, user_message: str, context: Optional[dict] = None):
        """Stream a chat response token by token (Ollama only)."""
        prompt = self.prompts.build_chat_response(
            user_message=user_message,
            history_summary=self._history_summary(),
        )

        if self.provider_name != "ollama":
            # Non-Ollama: yield the full response at once
            result = self._generate(WIZARD_SYSTEM, prompt)
            yield result or "I'm here."
            return

        import json
        import urllib.request

        url = os.environ.get("OLLAMA_HOST", "http://localhost:11434") + "/api/chat"
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": WIZARD_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            "stream": True,
            "think": False,
            "options": {"num_predict": 512},
        }).encode("utf-8")

        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    data = json.loads(line.decode("utf-8"))
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
        except Exception as e:
            yield f"I'm here. (Connection issue: {e})"

    # ─── LLM Generation ───────────────────────────────────────────────

    def _generate(self, system: str, prompt: str, max_tokens: int = 512) -> Optional[str]:
        """Generate via LLM. Uses native Ollama API for think:false support."""
        try:
            if self.provider_name == "ollama":
                return self._generate_ollama(system, prompt, max_tokens)
            else:
                return self._generate_openai_compat(system, prompt, max_tokens)
        except Exception as e:
            print(f"[Wizard] LLM error ({self.provider_name}): {e}")
            return None

    def _generate_ollama(self, system: str, prompt: str, max_tokens: int) -> Optional[str]:
        """Native Ollama API — supports think:false correctly."""
        import json
        import urllib.request

        url = os.environ.get("OLLAMA_HOST", "http://localhost:11434") + "/api/chat"
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "think": False,
            "options": {"num_predict": max_tokens},
        }).encode("utf-8")

        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("message", {}).get("content", "").strip()

    def _generate_openai_compat(self, system: str, prompt: str, max_tokens: int) -> Optional[str]:
        """OpenAI / Anthropic / OpenRouter — via existing llm_providers.py client."""
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
        )
        content = resp.choices[0].message.content
        return content.strip() if content else None

    # ─── Core Response ────────────────────────────────────────────────

    def respond_to_state(
        self,
        state: str,
        severity: int = 5,
        user_message: str = "",
        context: Optional[dict] = None,
    ) -> dict:
        context = context or {}
        context.setdefault("time_of_day", self._time_of_day())

        result: EngineResult = self.engine.recommend(
            state=state, severity=severity, context=context,
        )

        if result.protocol:
            return self._respond_protocol(result, state, severity, user_message, context)
        elif result.recommendations:
            return self._respond_intervention(result, state, severity, user_message, context)
        else:
            return self._respond_fallback(state, severity)

    def _respond_intervention(self, result, state, severity, user_message, context):
        top = result.recommendations[0]
        iv = top.intervention

        prompt = self.prompts.build_mood_response(
            state=state, severity=severity, user_message=user_message,
            intervention_name=iv.name, intervention_description=iv.description,
            intervention_steps=list(iv.steps), intervention_duration=iv.duration_seconds,
            context=context, history_summary=self._history_summary(state),
            alternatives=[r.intervention.name for r in result.recommendations[1:]],
        )
        wizard_message = self._generate(WIZARD_SYSTEM, prompt) or iv.wizard_intro

        return {
            "wizard_message": wizard_message,
            "llm_used": wizard_message != iv.wizard_intro,
            "intervention": {
                "id": iv.id, "name": iv.name, "family": iv.family.value,
                "duration_seconds": iv.duration_seconds, "format": iv.format.value,
                "steps": list(iv.steps),
                "wizard_intro": iv.wizard_intro, "wizard_outro": iv.wizard_outro,
            },
            "protocol": None,
            "session_config": self._session_config(iv),
            "alternatives": [
                {"id": r.intervention.id, "name": r.intervention.name, "reason": r.reason}
                for r in result.recommendations[1:]
            ],
        }

    def _respond_protocol(self, result, state, severity, user_message, context):
        protocol = result.protocol
        first_step = protocol.steps[0]
        first_iv = INTERVENTIONS.get(first_step.intervention_id) if first_step.intervention_id else None

        prompt = self.prompts.build_mood_response(
            state=state, severity=severity, user_message=user_message,
            intervention_name=first_iv.name if first_iv else "General support",
            intervention_description=first_iv.description if first_iv else "",
            intervention_steps=list(first_iv.steps) if first_iv else [],
            intervention_duration=first_iv.duration_seconds if first_iv else 0,
            context=context, history_summary=self._history_summary(state),
            protocol_name=protocol.name,
            protocol_steps=[
                INTERVENTIONS[s.intervention_id].name if s.intervention_id else "Check-in"
                for s in protocol.steps
            ],
        )
        wizard_message = self._generate(WIZARD_SYSTEM, prompt) or first_step.wizard_message

        return {
            "wizard_message": wizard_message,
            "llm_used": wizard_message != first_step.wizard_message,
            "intervention": {
                "id": first_iv.id, "name": first_iv.name, "family": first_iv.family.value,
                "duration_seconds": first_iv.duration_seconds, "format": first_iv.format.value,
                "steps": list(first_iv.steps),
            } if first_iv else None,
            "protocol": {
                "id": protocol.id, "name": protocol.name,
                "total_steps": len(protocol.steps), "current_step": 0,
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
            "session_config": self._session_config(first_iv) if first_iv else None,
            "alternatives": [],
        }

    def _respond_fallback(self, state, severity):
        return {
            "wizard_message": (
                f"I hear you. {state.capitalize()} at a {severity}/10 is real. "
                f"I'm here. You don't have to fix anything right now."
            ),
            "llm_used": False, "intervention": None,
            "protocol": None, "session_config": None, "alternatives": [],
        }

    # ─── Free-Form Chat ───────────────────────────────────────────────

    def chat(self, user_message: str, context: Optional[dict] = None) -> dict:
        prompt = self.prompts.build_chat_response(
            user_message=user_message,
            history_summary=self._history_summary(),
        )
        wizard_message = self._generate(WIZARD_SYSTEM, prompt)
        if not wizard_message:
            wizard_message = (
                "I'm here. Tell me more about what's going on. "
                "Or if you just need to vent — I'm listening. No judgment."
            )
        return {"wizard_message": wizard_message, "llm_used": wizard_message != ""}

    # ─── Celebration ──────────────────────────────────────────────────

    def celebrate_win(self, win_description: str) -> dict:
        iv = INTERVENTIONS[23]
        prompt = self.prompts.build_celebration(
            win_description=win_description,
            history_summary=self._history_summary(),
        )
        wizard_message = self._generate(WIZARD_SYSTEM, prompt) or iv.wizard_intro

        # Log to Hermes memory
        write_memory({
            "type": "win",
            "content": win_description,
            "source": "wellness_wizard",
        })

        return {
            "wizard_message": wizard_message,
            "intervention": {"id": iv.id, "name": iv.name, "steps": list(iv.steps)},
        }

    # ─── Preparation ──────────────────────────────────────────────────

    def prepare_for_stressor(self, stressor_description: str) -> dict:
        iv = INTERVENTIONS[24]
        prompt = self.prompts.build_preparation(
            stressor=stressor_description,
            history_summary=self._history_summary(),
        )
        wizard_message = self._generate(WIZARD_SYSTEM, prompt) or iv.wizard_intro
        return {
            "wizard_message": wizard_message,
            "intervention": {"id": iv.id, "name": iv.name, "steps": list(iv.steps)},
        }

    # ─── Dream Response ───────────────────────────────────────────────

    def respond_to_dream(self, dream_description: str, dream_tone: str = "neutral") -> dict:
        prompt = self.prompts.build_dream_response(dream_description, dream_tone)
        wizard_message = self._generate(WIZARD_SYSTEM, prompt)

        if not wizard_message:
            fallbacks = {
                "nightmare": "That sounds unsettling. You're safe. You're here. Let's ground you — 5 things you can see right now.",
                "positive": "A good dream! Hold onto that feeling. Want to write it down before it fades?",
                "neutral": "Interesting dream. What feeling stuck with you?",
            }
            wizard_message = fallbacks.get(dream_tone, fallbacks["neutral"])

        # Log to Hermes memory
        write_memory({
            "type": "dream",
            "content": dream_description,
            "tone": dream_tone,
            "source": "wellness_wizard",
        })

        return {"wizard_message": wizard_message, "suggested_interventions": [6, 8]}

    # ─── Post-Intervention Check-in ───────────────────────────────────

    def complete_intervention(
        self, intervention_id: int, state: str,
        severity_before: int, severity_after: Optional[int] = None,
        effectiveness_rating: Optional[int] = None, notes: str = "",
    ) -> dict:
        iv = INTERVENTIONS.get(intervention_id)
        if not iv:
            return {"wizard_message": "Thanks for checking in."}

        # Log to Hermes memory (the REAL memory system)
        write_memory({
            "type": "intervention",
            "content": f"{iv.name} for {state}",
            "intervention_id": intervention_id,
            "intervention_name": iv.name,
            "family": iv.family.value,
            "state": state,
            "severity_before": severity_before,
            "severity_after": severity_after,
            "effectiveness": effectiveness_rating,
            "notes": notes,
            "source": "wellness_wizard",
        })

        # LLM-powered check-in
        prompt = self.prompts.build_check_in(
            intervention_name=iv.name, state=state,
            severity_before=severity_before, severity_after=severity_after,
            effectiveness_rating=effectiveness_rating,
        )
        wizard_message = self._generate(WIZARD_SYSTEM, prompt) or iv.wizard_outro

        return {"wizard_message": wizard_message}

    # ─── Protocol Navigation ──────────────────────────────────────────

    def advance_protocol(self, protocol_id: str, current_step: int, feedback: Optional[str] = None) -> dict:
        from wellness.protocols import PROTOCOLS
        protocol = PROTOCOLS.get(protocol_id)
        if not protocol:
            return {"error": f"Unknown protocol: {protocol_id}"}

        next_idx = current_step + 1
        if next_idx >= len(protocol.steps):
            prompt = (
                f"The user completed the '{protocol.name}' protocol. "
                f"Celebrate their effort. Ask how they feel. Under 80 words."
            )
            msg = self._generate(WIZARD_SYSTEM, prompt) or f"You completed {protocol.name}. How are you feeling?"
            return {"wizard_message": msg, "protocol_complete": True, "next_step": None}

        next_step = protocol.steps[next_idx]
        iv = INTERVENTIONS.get(next_step.intervention_id) if next_step.intervention_id else None

        msg = None
        if iv:
            prompt = (
                f"Protocol '{protocol.name}', transitioning to: {iv.name}. "
                f"Context: {next_step.wizard_message}. Brief, warm. Under 60 words."
            )
            msg = self._generate(WIZARD_SYSTEM, prompt)
        if not msg:
            msg = next_step.wizard_message

        return {
            "wizard_message": msg, "protocol_complete": False,
            "next_step": {
                "step_number": next_idx,
                "intervention_id": next_step.intervention_id,
                "intervention_name": iv.name if iv else "Check-in",
                "is_check_in": next_step.is_check_in,
                "steps": list(iv.steps) if iv else [],
                "session_config": self._session_config(iv) if iv else None,
            },
        }

    # ─── Helpers ──────────────────────────────────────────────────────

    def _history_summary(self, state: str = None) -> str:
        """Real history only, with an explicit guard against invented memories."""
        try:
            parts = []
            if state:
                results = search_memory(f"mood {state}", limit=5)
                if results:
                    parts.append(f"they have logged '{state}' {len(results)} time(s) recently")
            interventions = search_memory("intervention", limit=5)
            names = [e.get("intervention_name") for e in interventions if e.get("intervention_name")]
            if names:
                parts.append(f"recent interventions: {', '.join(names)}")
            wins = search_memory("win", limit=3)
            if wins:
                parts.append(f"{len(wins)} win(s) celebrated recently")
            if parts:
                return " ".join(parts) + " Reference ONLY these facts, nothing else."
            return ("NONE. This is a fresh start. Do NOT mention any past sessions, "
                    "practices, patterns, or shared history. Speak only to this present moment.")
        except Exception:
            return "NONE. Do not reference any past events."

    def _session_config(self, iv: Optional[Intervention]) -> Optional[dict]:
        if not iv:
            return None
        config = {
            "intervention_id": iv.id, "name": iv.name,
            "format": iv.format.value, "duration_seconds": iv.duration_seconds,
            "steps": list(iv.steps),
        }
        if iv.family.value == "breathwork":
            if iv.id == 1:
                config["breathing_pattern"] = {"inhale": 4, "hold_in": 7, "exhale": 8, "hold_out": 0, "cycles": 4}
            elif iv.id == 2:
                config["breathing_pattern"] = {"inhale": 4, "hold_in": 4, "exhale": 4, "hold_out": 4, "cycles": 8}
        return config

    def _time_of_day(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        return "night"

    def status(self) -> dict:
        return {
            "llm_provider": self.provider_name,
            "llm_model": self.model,
            "interventions": len(INTERVENTIONS),
            "engine": "active",
        }
