"""
Hermes Life OS — Insights.
The wizard looks across what you've shared and reflects: what's helping,
what you've won, what it notices. Built on demo/storage.py memory.
"""
from __future__ import annotations

from storage import search_memory, get_recent_memory
from wellness.prompts import WIZARD_SYSTEM


def get_wins(limit: int = 12) -> list:
    wins = [w for w in search_memory("win", limit=limit) if w.get("type") == "win"]
    return [
        {"description": w.get("content") or w.get("description") or "A win",
         "timestamp": w.get("timestamp", "")}
        for w in wins
    ]


def get_effective_interventions() -> list:
    logs = [
        item for item in search_memory("intervention", limit=50)
        if item.get("type") == "intervention"
    ]
    by_name: dict = {}
    for item in logs:
        name = item.get("intervention_name") or "A practice"
        entry = by_name.setdefault(
            name,
            {"name": name, "times_used": 0, "improvements": [], "state": item.get("state")},
        )
        entry["times_used"] += 1
        before, after = item.get("severity_before"), item.get("severity_after")
        if isinstance(before, (int, float)) and isinstance(after, (int, float)):
            entry["improvements"].append(before - after)
    result = []
    for name, d in by_name.items():
        avg = round(sum(d["improvements"]) / len(d["improvements"]), 1) if d["improvements"] else None
        result.append({"name": name, "times_used": d["times_used"],
                       "avg_improvement": avg, "state": d["state"]})
    result.sort(key=lambda x: (x["avg_improvement"] if x["avg_improvement"] is not None else -99),
                reverse=True)
    return result[:5]

def _recent_summary() -> str:
    """A compact factual digest of the last 7 days for the reflection prompt."""
    entries = get_recent_memory(days=7)
    if not entries:
        return "No history yet — this is a brand new companion."
    lines = []
    moods = [e for e in entries if e.get("type") == "mood"]
    if moods:
        states: dict = {}
        for m in moods:
            s = m.get("state", "?")
            states[s] = states.get(s, 0) + 1
        lines.append("Moods logged: " + ", ".join(f"{k} ({v})" for k, v in states.items()))
    interventions = [e for e in entries if e.get("type") == "intervention"]
    if interventions:
        names: dict = {}
        for i in interventions:
            n = i.get("intervention_name", "?")
            names[n] = names.get(n, 0) + 1
        lines.append("Interventions used: " + ", ".join(f"{k} ({v})" for k, v in names.items()))
    wins = [e for e in entries if e.get("type") == "win"]
    if wins:
        lines.append(f"Wins celebrated: {len(wins)}")
    sleeps = [e for e in entries if e.get("type") == "sleep"]
    hrs = [s.get("hours") for s in sleeps if isinstance(s.get("hours"), (int, float))]
    if hrs:
        lines.append(f"Sleep logged: avg {round(sum(hrs) / len(hrs), 1)}h over {len(hrs)} night(s)")
    hydration = [e for e in entries if e.get("type") == "hydration"]
    if hydration:
        lines.append(f"Hydration logged {len(hydration)} time(s)")
    return "\n".join(lines) if lines else "Very little shared yet."


def reflect_stream(wizard):
    """Stream a warm reflection on what the wizard has noticed lately."""
    summary = _recent_summary()
    prompt = f"""Look back over what this person has shared with you recently, and reflect warmly on what you notice.

Here is the factual record of the last 7 days:
{summary}

Speak directly to them in your warm, wise voice. Name one or two things you notice — a pattern, a strength, something worth celebrating, or something to be gentle about. Reference ONLY what is in the record above; if there is little data, acknowledge that warmly and invite them to keep sharing. Keep it to two or three sentences, under 60 words. Be warm and specific, not sweeping. You may end with a gentle invitation, but you do not have to. No markdown, no lists."""

    streamed = False
    if wizard.provider_name == "ollama":
        from wellness.streaming import _stream_ollama
        for token in _stream_ollama(wizard.model, WIZARD_SYSTEM, prompt, max_tokens=160):
            streamed = True
            yield {"type": "token", "text": token}
    else:
        msg = wizard._generate(WIZARD_SYSTEM, prompt)
        if msg:
            streamed = True
            yield {"type": "token", "text": msg}
    if not streamed:
        yield {"type": "token",
               "text": "I'm just getting to know you. Keep sharing with me — I'm watching, and I care."}
    yield {"type": "done"}


def _recent_signature() -> str:
    """Cheap fingerprint of the last 7 days; changes whenever new data lands."""
    entries = get_recent_memory(days=7)

    def n(t):
        return sum(1 for e in entries if e.get("type") == t)

    last_ts = entries[-1].get("timestamp", "") if entries else ""
    return (
        f"{n('mood')}|{n('intervention')}|{n('win')}|"
        f"{n('sleep')}|{n('hydration')}|{last_ts}"
    )


def get_insights_summary() -> dict:
    return {
        "wins": get_wins(),
        "effective": get_effective_interventions(),
        "signature": _recent_signature(),
    }
