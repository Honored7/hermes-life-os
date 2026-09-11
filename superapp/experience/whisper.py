# Whispers — one line per context, the ambient companion voice.
#
# Not a chatbot: a single specific sentence rendered inside a Life card
# or Today, composed deterministically from the week's facts plus the
# strongest related correlation (if the data can carry one). Empty data
# yields an invitation, never filler wisdom. The full conversation stays
# behind "sit with me".

from __future__ import annotations

from typing import Any

# intelligence metric -> Life dimension ids it may garnish
_METRIC_DIMS = {
    "sleep": ("sleep",),
    "hydration": ("hydration",),
    "mood": ("mood", "mental"),
    "stress": ("mental", "mood"),
    "energy": ("fitness", "mood"),
}


def _related_correlations(dimension: str) -> list[dict[str, Any]]:
    try:
        from superapp.experience import store
        from superapp.intelligence.patterns import correlations

        mem = store.get_recent_memory(days=30) or []
        out = []
        for c in correlations(mem):
            dims = set(_METRIC_DIMS.get(c["metric_a"], ())) | set(
                _METRIC_DIMS.get(c["metric_b"], ()))
            if dimension in dims:
                out.append(c)
        return out
    except Exception:
        return []


def _garnish(dimension: str) -> str:
    corrs = _related_correlations(dimension)
    if not corrs:
        return ""
    top = corrs[0]
    other = top["metric_b"] if top["metric_a"] in ("sleep", "mood",
                                                  "stress") else top["metric_a"]
    verb = "rise together" if top["direction"] == "positive" \
        else "move in opposite directions"
    return (f" Your {top['metric_a']} and {other} {verb} lately "
            f"(r={top['r']}).")


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def whisper(dimension: str | None = None) -> dict[str, Any]:
    """One specific line for a dimension (or 'today')."""
    from superapp.experience import dimension_stats

    dim = (dimension or "today").strip().lower()
    if dim == "today":
        return {"dimension": "today", "text": _today_whisper()}
    try:
        stats = dimension_stats()
    except Exception:
        stats = {}
    card = stats.get(dim) or {}
    week = card.get("week") or {}
    text = _DIM_WHISPERS.get(dim, _generic)(card, week)
    return {"dimension": dim, "text": text + _garnish(dim)}


def _today_whisper() -> str:
    try:
        from superapp.experience import mirror

        reflection = (mirror().get("reflection") or "").strip()
    except Exception:
        reflection = ""
    if reflection and "gathering" not in reflection:
        return reflection
    return ("A fresh page. Name one feeling, log one glass, "
            "and the companion starts learning your shape.")


def _generic(card: dict, week: dict) -> str:
    return "Live a little longer here and this line starts speaking."


def _sleep(card: dict, week: dict) -> str:
    avg = week.get("avg_hours")
    if avg is None:
        return "No nights logged yet — the first one starts the rhythm."
    if avg < 6.5:
        return (f"Sleep has averaged {avg}h lately. Even thirty more "
                "minutes changes tomorrow.")
    return (f"{avg}h on average lately — protected rest, quietly powering "
            "everything else.")


def _hydration(card: dict, week: dict) -> str:
    today = _num(card.get("today"))
    goal = _num(card.get("target")) or 8
    if today <= 0:
        return "Not a glass counted today — the first one is the kindest."
    if today < goal:
        return (f"{int(today)} of {int(goal)} glasses so far. "
                "One more would land well.")
    return "Well-watered today. Small, steady, unglamorous — exactly right."


def _mental(card: dict, week: dict) -> str:
    avg = week.get("avg_stress")
    if avg is None:
        return ("Nothing named yet. A heavy feeling, written down, "
                "is already half tended.")
    if avg >= 6:
        return (f"Stress has sat near {avg}/10 this week. Naming the "
                "weight is the first kindness.")
    return "A steadier inner week. Whatever gave your mind air — keep it."


def _mood(card: dict, week: dict) -> str:
    return ("Your weather, named day by day. The mirror in Insights "
            "reads the whole sky.")


def _fitness(card: dict, week: dict) -> str:
    n = (week.get("workouts") or 0)
    if not n:
        return ("No movement logged this week. Five minutes counts — "
                "the bar starts wherever you are.")
    return (f"{n} workout(s) this week. Motion is medicine; "
            "you've been taking it.")


def _focus(card: dict, week: dict) -> str:
    mins = _num(week.get("total_min"))
    if mins <= 0:
        return ("No quiet blocks protected yet. Twenty minutes, one "
                "thing — that's a beginning.")
    return (f"{int(mins)} deep minutes this week. Protected attention "
            "is rare; you're making it.")


def _nutrition(card: dict, week: dict) -> str:
    n = (week.get("meals") or 0)
    if not n:
        return ("Nothing noted yet. No scores here — just noticing what "
                "feeds you.")
    return (f"{n} meal(s) noted this week. Regular, gentle, enough.")


def _habits(card: dict, week: dict) -> str:
    n = (week.get("active") or 0)
    if not n:
        return ("No live threads right now. One small daily kindness "
                "would give the days a thread.")
    return (f"{n} thread(s) alive. Consistency is the whole game; "
            "you're playing.")


def _goals(card: dict, week: dict) -> str:
    n = (week.get("active") or 0)
    if not n:
        return ("Nothing aimed at yet. A goal can be tiny: one walk "
                "this week.")
    return (f"{n} aim(s) in motion, step by unglamorous step.")


def _spending(card: dict, week: dict) -> str:
    total = week.get("total")
    if total is None:
        return ("Nothing counted yet. Noticing where money goes is "
                "calm, not judgment.")
    top = week.get("top_category")
    tail = f" Most of it goes to {top}." if top else ""
    return (f"About ${total:.0f} this week.{tail} Averages, not alarms.")


def _social(card: dict, week: dict) -> str:
    n = (week.get("moments") or 0)
    if not n:
        return ("No moments with people logged. One reaching-out "
                "counts double.")
    q = week.get("avg_quality")
    tail = f" averaging {q}/10" if q else ""
    return (f"{n} moment(s) with people this week{tail}. "
            "Notice who lifts you.")


def _substance(card: dict, week: dict) -> str:
    n = (week.get("entries") or 0)
    if not n:
        return ("Nothing logged. If you ever wonder about a habit, "
                "this page only ever shows you facts.")
    return (f"{n} logged this week. Facts, not shame — patterns "
            "you can actually use.")


def _reading(card: dict, week: dict) -> str:
    mins = _num(week.get("total_min"))
    if mins <= 0:
        return ("No pages lately. Ten quiet minutes with a book is "
                "stillness you can keep.")
    return (f"{int(mins)} quiet minutes this week. Stillness, kept.")


def _medication(card: dict, week: dict) -> str:
    pct = week.get("adherence_pct")
    if pct is None:
        return ("Nothing tracked yet. Tending yourself on schedule "
                "is care, not chore.")
    if pct >= 80:
        return (f"{pct}% kept this week. Faithful tending — "
                "your future self thanks you.")
    return (f"{pct}% kept this week. Missed doses happen; "
            "tomorrow is a clean page.")


_DIM_WHISPERS = {
    "sleep": _sleep,
    "hydration": _hydration,
    "mental": _mental,
    "mood": _mood,
    "fitness": _fitness,
    "focus": _focus,
    "nutrition": _nutrition,
    "habits": _habits,
    "goals": _goals,
    "spending": _spending,
    "social": _social,
    "substance": _substance,
    "reading": _reading,
    "medication": _medication,
}
