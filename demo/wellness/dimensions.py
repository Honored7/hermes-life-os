"""
The dimension mind — what each Life card sees, and how the dimensions see
each other.

Every figure is read from real logs; every cross-dimension sentence is a
guarded correlation over paired days (minimum sample, direction checked),
so the wizard only ever claims a connection the data can carry. Sleep is
sourced from the eyes (the sleep store) so it agrees with the Rhythm card
and the check-in voice; the rest are read generically from the memory
journal, tolerantly, so a card lights up as data arrives and never crashes
when a store is empty or shaped differently than expected.
"""
from __future__ import annotations

from datetime import date

from wellness.insights import mood_weather
from wellness.vitals import sleep_summary

LABEL = {
    "nutrition": "nutrition", "sleep": "sleep", "hydration": "hydration",
    "fitness": "movement", "mental": "your mind", "focus": "focus",
    "habits": "your habits", "goals": "your goals", "mood": "your mood",
}
TYPES = {
    "nutrition": ["nutrition"], "hydration": ["hydration"],
    "fitness": ["workout", "fitness"], "mental": ["mental"],
    "focus": ["focus"], "habits": ["habit", "habits"],
    "goals": ["goal", "goals"], "mood": ["mood"],
}
VALUE_KEYS = {
    "nutrition": ["quality", "value", "calories"], "hydration": ["glasses", "value"],
    "fitness": ["quality", "value", "minutes"], "mental": ["quality", "value", "severity"],
    "focus": ["quality", "value"], "habits": ["quality", "value", "count"],
    "goals": ["quality", "value"], "mood": ["severity", "value"],
}
# polarity for correlation: True = a higher value is the "good" direction
HIGHER_BETTER = {
    "sleep": True, "focus": True, "fitness": True, "hydration": True,
    "nutrition": True, "habits": True, "goals": True, "mental": True, "mood": False,
}
# (driver, dependent) pairs the wizard watches for a quiet connection
PAIRS = [("sleep", "focus"), ("sleep", "mood"), ("fitness", "mood"),
         ("hydration", "focus"), ("nutrition", "fitness")]


def _today_str() -> str:
    return date.today().isoformat()


def _entry_date(e: dict) -> str:
    d = e.get("date")
    if d:
        return str(d)
    return str(e.get("timestamp", ""))[:10]


def _num(e: dict, keys: list):
    for k in keys:
        v = e.get(k)
        if v is None:
            continue
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


def _memory():
    try:
        from storage import get_recent_memory
        return get_recent_memory(days=30)
    except Exception:
        return []


def _series_for(dim: str, mem: list) -> dict:
    """date -> averaged value for a dimension, read tolerantly."""
    keys = VALUE_KEYS.get(dim, ["value"])
    by_date: dict = {}
    for e in mem:
        if e.get("type") not in TYPES.get(dim, []) and e.get("dimension") != dim:
            continue
        v = _num(e, keys)
        if v is None:
            continue
        d = _entry_date(e)
        if not d:
            continue
        by_date.setdefault(d, []).append(v)
    return {d: round(sum(vs) / len(vs), 2) for d, vs in by_date.items()}


def _mood_series(mem: list) -> dict:
    by_date: dict = {}
    for e in mem:
        if e.get("type") != "mood" or e.get("severity") is None:
            continue
        try:
            sev = float(e["severity"])
        except (TypeError, ValueError):
            continue
        d = _entry_date(e)
        if d:
            by_date.setdefault(d, []).append(sev)
    return {d: round(sum(vs) / len(vs), 2) for d, vs in by_date.items()}


def _shape(series: dict, last_n: int = 14) -> dict:
    items = sorted(series.items())[-last_n:]
    today = _today_str()
    series_out = [{"date": d, "value": v} for d, v in items]
    return {
        "series": series_out,
        "today": series.get(today),
        "latest": items[-1][1] if items else None,
    }


def _edges(series_by_dim: dict) -> dict:
    """Guarded cross-dimension connections, keyed by the dependent dimension."""
    edges: dict = {}
    for driver, dependent in PAIRS:
        if dependent in edges:
            continue
        ds = series_by_dim.get(driver, {})
        es = series_by_dim.get(dependent, {})
        common = sorted(set(ds) & set(es))
        if len(common) < 3:
            continue
        dvals = [ds[d] for d in common]
        med = sorted(dvals)[len(dvals) // 2]
        low = [d for d in common if ds[d] < med]
        high = [d for d in common if ds[d] >= med]
        if len(low) < 2 or len(high) < 2:
            continue
        dep_low = sum(es[d] for d in low) / len(low)
        dep_high = sum(es[d] for d in high) / len(high)
        hb = HIGHER_BETTER.get(dependent, True)
        worse_on_low = (dep_low < dep_high) if hb else (dep_low > dep_high)
        if worse_on_low and abs(dep_low - dep_high) >= 1.0:
            edges[dependent] = (
                f"When your {LABEL[driver]} runs low, your {LABEL[dependent]} tends to "
                f"feel it too — tending to {LABEL[driver]} may be a quiet lever."
            )
    return edges


def dimension_stats() -> dict:
    mem = _memory()

    series_by_dim = {dim: _series_for(dim, mem) for dim in TYPES}
    series_by_dim["sleep"] = {}  # sleep sourced from the eyes below
    series_by_dim["mood"] = _mood_series(mem)

    dims = {dim: _shape(s) for dim, s in series_by_dim.items()}

    # sleep: the eyes are the source of truth (agrees with Rhythm + check-in)
    try:
        s = sleep_summary()
        sleep_series = [{"date": p["date"], "value": p["hours"]} for p in s.get("series", [])]
        dims["sleep"] = {"series": sleep_series, "today": None, "latest": s.get("last_hours")}
        sleep_summary_out = {"avg": s.get("avg_hours"), "streak": s.get("poor_streak", 0),
                             "count": s.get("count", 0)}
    except Exception:
        sleep_summary_out = {"avg": None, "streak": 0, "count": 0}

    # mood: richer headline from the weather
    try:
        w = mood_weather(days=7)
        mood_summary_out = {"predominant": w.get("predominant"),
                            "temperature": w.get("temperature"), "total": w.get("total", 0)}
    except Exception:
        mood_summary_out = {"predominant": None, "temperature": None, "total": 0}

    return {
        "dims": dims,
        "edges": _edges(series_by_dim),
        "sleep": sleep_summary_out,
        "mood": mood_summary_out,
    }
