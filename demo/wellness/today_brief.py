"""
The companion at the door.
A time-aware greeting, one specific true line, and a single gentle suggestion —
computed from what is actually true for you today.
"""
from __future__ import annotations
import time as _t


def _n(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _suggestion(stats):
    hyd = stats.get("hydration") or {}
    goal = _n(hyd.get("goal")) or 8
    water = _n(hyd.get("today"))
    fit = _n((stats.get("fitness") or {}).get("today"))
    foc = _n((stats.get("focus") or {}).get("today"))
    if water < goal:
        return {"text": "a glass of water would land well.", "kind": "water", "payload": {"glasses": 1}}
    if foc < 20:
        return {"text": "twenty quiet minutes?", "kind": "focus", "payload": {"task": "Quiet block", "duration_min": 20}}
    if fit < 10:
        return {"text": "a short walk would count.", "kind": "fitness", "payload": {"workout_type": "walk", "duration_min": 10}}
    return {"text": "a moment to breathe?", "kind": "breathe", "payload": {"pattern": "unwind"}}


def briefing():
    from wellness import life_stats as LS
    from storage import load_habits
    hour = _t.localtime().tm_hour
    part = "morning" if hour < 12 else ("afternoon" if hour < 17 else "evening")
    greeting = {"morning": "Good morning", "afternoon": "Good afternoon", "evening": "Good evening"}[part]

    stats = LS.dimension_stats()
    sleep_now = _n((stats.get("sleep") or {}).get("today"))
    water = _n((stats.get("hydration") or {}).get("today"))
    habits = load_habits() or []
    alive = sum(1 for h in habits if _n(h.get("streak")) > 0)

    bits = []
    if sleep_now:
        bits.append(f"you slept {sleep_now}h last night")
    if alive:
        bits.append(f"{alive} habit{'s' if alive != 1 else ''} still alive")
    if water:
        bits.append(f"{int(water)} glass{'es' if water != 1 else ''} of water so far")
    true_line = (greeting + ". " + ", ".join(bits) + ".") if bits else (greeting + ". A fresh page — what will you tend first?")

    return {
        "part": part,
        "greeting": greeting,
        "hour": hour,
        "evening": part == "evening",
        "true_line": true_line,
        "suggestion": _suggestion(stats),
    }


def alive():
    """A glance at what's breathing today: live habits, moving goals, movement."""
    from datetime import date
    from storage import load_habits, load_goals, load_fitness
    today = date.today().isoformat()
    habits = load_habits() or []
    goals = load_goals() or []
    move = sum(_n(f.get("duration")) for f in (load_fitness() or []) if str(f.get("date")) == today)
    active = [str(h.get("name")).strip() for h in habits if _n(h.get("streak")) > 0 and str(h.get("name") or "").strip()][:3]
    moving = [{"name": str(g.get("name")), "progress": round(_n(g.get("progress"))) }
              for g in goals if 0 < _n(g.get("progress")) < 100][:3]
    return {"habits": active, "goals": moving, "move_min": int(move)}
