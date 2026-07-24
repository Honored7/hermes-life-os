"""
Streaming check-in.

The engine decides the intervention/protocol instantly (no LLM), so the
card or journey can appear immediately — then the wizard's voice streams
in over it. Enforces a hard guard against invented memories: the wizard
is told exactly what history exists and forbidden from referencing more.
"""
from __future__ import annotations

import json
import os
import urllib.request

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
      {"type":"token","text":...}   — the wizard's words, chunk by chunk
      {"type":"done"}
    """
    context = dict(context or {})
    context.setdefault("time_of_day", wizard._time_of_day())

    result = wizard.engine.recommend(state=state, severity=severity, context=context)
    history = _safe_history(wizard, state)

    meta = {"intervention": None, "protocol": None, "session_config": None, "alternatives": []}
    prompt = None
    fallback = f"I hear you. {state.capitalize()} at a {severity}/10 is real. I'm here with you."

    if result.protocol:
        protocol = result.protocol
        first = protocol.steps[0]
        first_iv = INTERVENTIONS.get(first.intervention_id) if first.intervention_id else None

        # Full journey data so the frontend can walk the whole path
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

        prompt = wizard.prompts.build_mood_response(
            state=state, severity=severity, user_message=user_message,
            intervention_name=first_iv.name if first_iv else "General support",
            intervention_description=first_iv.description if first_iv else "",
            intervention_steps=list(first_iv.steps) if first_iv else [],
            intervention_duration=first_iv.duration_seconds if first_iv else 0,
            context=context, history_summary=history,
            protocol_name=protocol.name,
            protocol_steps=[
                INTERVENTIONS[s.intervention_id].name if s.intervention_id else "Check-in"
                for s in protocol.steps
            ],
        )
        fallback = first.wizard_message

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
