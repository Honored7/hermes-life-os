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
    preps = [e for e in entries if e.get("type") == "preparation"]
    if preps:
        last = (preps[-1].get("content") or "")[:60]
        lines.append(
            f"They steadied themselves before something {len(preps)} time(s) recently"
            + (f" (e.g. {last})" if last else "")
            + "."
        )
    try:
        from wellness.vitals import sleep_summary as _ss, detect_sleep_mood_pattern as _pat
        _s = _ss()
        if _s["count"]:
            note = "Sleep: they have logged " + str(_s["count"]) + " night(s); recent average " + str(_s["avg_hours"]) + "h"
            if _s["poor_streak"] >= 2:
                note += "; " + str(_s["poor_streak"]) + " short night(s) in a row"
            lines.append(note + ".")
            _p = _pat()
            if _p:
                lines.append("Pattern noticed: " + _p)
    except Exception:
        pass
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

STATES = ["good", "neutral", "stressed", "anxious", "sad", "angry", "low_energy", "lonely"]


def mood_weather(days: int = 7) -> dict:
    """Distribution of moods over the last N days — the data behind the Today aura."""
    try:
        entries = get_recent_memory(days=days)
    except Exception:
        entries = []
    moods = [e for e in entries if e.get("type") == "mood" and e.get("state")]
    counts = {st: 0 for st in STATES}
    sev = []
    for e in moods:
        st = e.get("state")
        if st in counts:
            counts[st] += 1
        if e.get("severity") is not None:
            try:
                sev.append(float(e["severity"]))
            except (TypeError, ValueError):
                pass
    total = sum(counts.values())
    predominant = max(counts, key=counts.get) if total else None
    spread = len([c for c in counts.values() if c > 0])
    temperature = round(sum(sev) / len(sev), 1) if sev else None
    return {
        "total": total,
        "days": days,
        "predominant": predominant,
        "predominant_count": counts.get(predominant, 0) if predominant else 0,
        "spread": spread,
        "temperature": temperature,
        "counts": counts,
    }


# valence per mood — the axis the tone-shift verdict reads (warm vs cool)
VALENCE = {
    "good": 2, "neutral": 1,
    "stressed": -1, "low_energy": -1,
    "anxious": -2, "sad": -2, "angry": -2, "lonely": -2,
}
STATE_WORD = {
    "good": "joyful", "neutral": "calm", "stressed": "stressed",
    "anxious": "anxious", "sad": "sad", "angry": "angry",
    "low_energy": "drained", "lonely": "lonely",
}


def _date_of(e) -> str:
    d = e.get("date")
    return str(d) if d else str(e.get("timestamp", ""))[:10]


def mood_trend(days: int = 21) -> dict:
    """The emotional mirror: an intensity line (colour = mood) plus a
    valence-based tone-shift verdict that can never contradict it."""
    from datetime import date as _date, timedelta
    try:
        entries = get_recent_memory(days=days)
    except Exception:
        entries = []

    rows = []  # (date_str, state, severity)
    for e in entries:
        if e.get("type") != "mood" or not e.get("state") or e.get("severity") is None:
            continue
        d = _date_of(e)
        if not d:
            continue
        try:
            rows.append((d, e["state"], float(e["severity"])))
        except (TypeError, ValueError):
            continue

    by = {}
    for d, st, sev in rows:
        by.setdefault(d, {"sevs": [], "states": []})
        by[d]["sevs"].append(sev)
        by[d]["states"].append(st)
    series = []
    for d in sorted(by):
        sevs, states = by[d]["sevs"], by[d]["states"]
        series.append({
            "date": d,
            "severity": round(sum(sevs) / len(sevs), 1),
            "state": max(set(states), key=states.count),
        })
    series = series[-days:]

    today = _date.today()
    this_rows = [r for r in rows if (today - timedelta(days=6)).isoformat() <= r[0] <= today.isoformat()]
    last_rows = [r for r in rows if (today - timedelta(days=13)).isoformat() <= r[0] <= (today - timedelta(days=7)).isoformat()]

    def vavg(rs):
        return sum(VALENCE.get(st, 0) for _, st, _ in rs) / len(rs) if rs else None

    def pred(rs):
        sts = [st for _, st, _ in rs]
        return max(set(sts), key=sts.count) if sts else None

    tv, lv = vavg(this_rows), vavg(last_rows)
    if tv is None or lv is None:
        direction, delta = "none", None
    else:
        delta = round(tv - lv, 2)
        direction = "warmer" if delta >= 0.6 else ("cooler" if delta <= -0.6 else "holding")

    tw = STATE_WORD.get(pred(this_rows), "your days")
    lw = STATE_WORD.get(pred(last_rows), "before")
    verdict = {
        "none": "Not quite two weeks of check-ins yet — the mirror is still clearing. Keep naming how you feel, and a shape will form.",
        "holding": f"About the same ground as last week — {tw}, holding steady. There is a quiet strength in that consistency.",
        "warmer": f"The tone of your week has warmed — {lw} giving way to more {tw}. Whatever you have been doing, some of it is landing.",
        "cooler": f"A cooler week than the last — more {tw} than {lw}. That is worth tending gently, not fixing in a hurry.",
    }[direction]

    this_intensity = round(sum(s for _, _, s in this_rows) / len(this_rows), 1) if this_rows else None
    return {
        "series": series,
        "direction": direction,
        "delta": delta,
        "verdict": verdict,
        "this_predominant": pred(this_rows),
        "last_predominant": pred(last_rows),
        "this_intensity": this_intensity,
        "this_count": len(this_rows),
        "last_count": len(last_rows),
    }
