"""
Streaming check-in + journey narration.

- respond_stream: engine decides instantly; for a single intervention the
  wizard's opening streams over it. For a protocol, the journey itself
  narrates (no separate opening monologue) — faster for someone in crisis.
- narrate_step_stream: fresh, personal narration for each journey step,
  paraphrasing the step's essence so it never repeats verbatim.
- _safe_history: hard guard against invented memories.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request

from storage import write_memory

from wellness.interventions import INTERVENTIONS
from wellness.prompts import WIZARD_SYSTEM


def _safe_history(wizard, state=None):
    try:
        from storage import search_memory
        parts = []
        if state:
            r = search_memory(f"mood {state}", limit=5)
            if r:
                parts.append(f"they have logged '{state}' {len(r)} time(s) recently")
        iv = search_memory("intervention", limit=5)
        names = [e.get("intervention_name") for e in iv if e.get("intervention_name")]
        if names:
            parts.append(f"recent interventions: {', '.join(names)}")
        wins = search_memory("win", limit=3)
        if wins:
            parts.append(f"{len(wins)} win(s) celebrated recently")
        if parts:
            return " ".join(parts) + " — reference ONLY these facts, nothing else."
        return ("NONE. This is a fresh start. Do NOT mention any past sessions, "
                "practices, patterns, or shared history. Speak only to this present moment.")
    except Exception:
        return "NONE. Do not reference any past events."


def _stream_ollama(model, system, prompt, max_tokens=512):
    url = os.environ.get("OLLAMA_HOST", "http://localhost:11434") + "/api/chat"
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": True,
        "think": False,
        "options": {"num_predict": max_tokens},
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            for line in resp:
                data = json.loads(line.decode("utf-8"))
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content
    except Exception as e:
        yield f" (I'm having trouble finding my voice right now — {e})"


def _intervention_payload(iv):
    return {
        "id": iv.id, "name": iv.name, "family": iv.family.value,
        "duration_seconds": iv.duration_seconds, "format": iv.format.value,
        "steps": list(iv.steps),
        "wizard_intro": iv.wizard_intro, "wizard_outro": iv.wizard_outro,
    }


def respond_stream(wizard, state, severity=5, user_message="", context=None):
    """
    Yields:
      {"type":"meta","data":{...}}  — intervention or full protocol journey (instant)
      {"type":"token","text":...}   — the wizard's words (single interventions only)
      {"type":"done"}
    """
    context = dict(context or {})
    context.setdefault("time_of_day", wizard._time_of_day())

    result = wizard.engine.recommend(state=state, severity=severity, context=context)
    history = _safe_history(wizard, state)

    # Remember the check-in so reflections and trends have mood data
    try:
        write_memory({"type": "mood", "state": state, "severity": severity,
                      "note": user_message, "date": time.strftime("%Y-%m-%d")})
    except Exception:
        pass

    meta = {"intervention": None, "protocol": None, "session_config": None, "alternatives": []}
    prompt = None
    fallback = f"I hear you. {state.capitalize()} at a {severity}/10 is real. I'm here with you."

    if result.protocol:
        protocol = result.protocol
        first = protocol.steps[0]
        first_iv = INTERVENTIONS.get(first.intervention_id) if first.intervention_id else None

        steps_data = []
        for i, s in enumerate(protocol.steps):
            iv = INTERVENTIONS.get(s.intervention_id) if s.intervention_id else None
            steps_data.append({
                "step_number": i,
                "intervention_id": s.intervention_id,
                "intervention_name": iv.name if iv else "Check-in",
                "wizard_message": s.wizard_message,
                "is_check_in": s.is_check_in,
                "intervention": _intervention_payload(iv) if iv else None,
                "session_config": wizard._session_config(iv) if iv else None,
            })

        meta["protocol"] = {
            "id": protocol.id,
            "name": protocol.name,
            "trigger_state": protocol.trigger_state,
            "total_steps": len(protocol.steps),
            "current_step": 0,
            "steps": steps_data,
        }
        if first_iv:
            meta["intervention"] = _intervention_payload(first_iv)
            meta["session_config"] = wizard._session_config(first_iv)

        # The journey narrates itself — no opening monologue for someone in crisis.
        yield {"type": "meta", "data": meta}
        yield {"type": "done"}
        return

    elif result.recommendations:
        top = result.recommendations[0]
        iv = top.intervention
        meta["intervention"] = _intervention_payload(iv)
        meta["session_config"] = wizard._session_config(iv)
        meta["alternatives"] = [
            {"id": r.intervention.id, "name": r.intervention.name, "reason": r.reason}
            for r in result.recommendations[1:]
        ]
        prompt = wizard.prompts.build_mood_response(
            state=state, severity=severity, user_message=user_message,
            intervention_name=iv.name, intervention_description=iv.description,
            intervention_steps=list(iv.steps), intervention_duration=iv.duration_seconds,
            context=context, history_summary=history,
            alternatives=[r.intervention.name for r in result.recommendations[1:]],
        )
        fallback = iv.wizard_intro

    yield {"type": "meta", "data": meta}

    if prompt is not None and wizard.provider_name == "ollama":
        streamed = False
        for token in _stream_ollama(wizard.model, WIZARD_SYSTEM, prompt):
            streamed = True
            yield {"type": "token", "text": token}
        if not streamed:
            yield {"type": "token", "text": fallback}
    elif prompt is not None:
        msg = wizard._generate(WIZARD_SYSTEM, prompt)
        yield {"type": "token", "text": msg or fallback}
    else:
        yield {"type": "token", "text": fallback}

    yield {"type": "done"}


def narrate_step_stream(wizard, protocol_id, step_number, state, severity=5, user_message=""):
    """
    Fresh narration for one journey step. Paraphrases the step's essence
    (never verbatim), acknowledges the step just completed, and keeps the
    gentle-coach "go do it" energy.
    """
    from wellness.protocols import PROTOCOLS
    protocol = PROTOCOLS.get(protocol_id)
    if not protocol or step_number >= len(protocol.steps):
        yield {"type": "token", "text": "Let's keep going."}
        yield {"type": "done"}
        return

    step = protocol.steps[step_number]
    iv = INTERVENTIONS.get(step.intervention_id) if step.intervention_id else None
    history = _safe_history(wizard, state)

    if step_number > 0:
        prev = protocol.steps[step_number - 1]
        prev_iv = INTERVENTIONS.get(prev.intervention_id) if prev.intervention_id else None
        prev_name = prev_iv.name if prev_iv else "the previous step"
        prev_line = f"They just finished: {prev_name}. Acknowledge that briefly."
    else:
        prev_line = "This is the first step — they've just committed to the journey."

    step_name = iv.name if iv else "a check-in"

    if step.is_check_in:
        guidance = (
            "This is the final check-in. Warmly invite them to notice where the feeling "
            "is now compared to where it started, and to rate it. Honor the effort they just gave."
        )
    else:
        guidance = (
            "Be a gentle coach: warm, but clear and a little directive. Tell them what to do "
            "and nudge them to go do it now. Short sentences carry urgency better than long ones."
        )

    note_line = f'\nWhen they checked in, they said: "{user_message}"' if user_message else ""

    prompt = f"""You are walking someone through the "{protocol.name}" journey because they're feeling {state} ({severity}/10).

{prev_line}
Now guide them into: {step_name}.

The core of what this step must convey — say it fresh in your own voice, do NOT repeat it word-for-word:
"{step.wizard_message}"

{guidance}
{note_line}
{history}

Keep it under 60 words. Speak directly to them. No markdown, no lists."""

    streamed = False
    if wizard.provider_name == "ollama":
        for token in _stream_ollama(wizard.model, WIZARD_SYSTEM, prompt):
            streamed = True
            yield {"type": "token", "text": token}
    else:
        msg = wizard._generate(WIZARD_SYSTEM, prompt)
        if msg:
            streamed = True
            yield {"type": "token", "text": msg}
    if not streamed:
        yield {"type": "token", "text": step.wizard_message}
    yield {"type": "done"}
