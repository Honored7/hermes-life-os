"""
Per-dimension records — the real data behind each Life card.

Goals come back enriched by the goal engine: computed count/target/%, a
plain-English pace line, and a suggested habit. Nothing here asks the user
to self-report a percentage.
"""
from __future__ import annotations
from wellness import goals as G


def _safe(fn):
    try:
        return fn() or []
    except Exception:
        return []


def _load(name):
    import storage
    return _safe(getattr(storage, "load_" + name))


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def dimension_records() -> dict:
    raw_goals = [g for g in _load("goals") if (g.get("name") or "").strip()]
    goals = [G.compute_goal(g) for g in raw_goals]
    habits = _load("habits")
    nutrition = _load("nutrition")
    fitness = _load("fitness")
    focus = _load("focus")
    mental = _load("mental")

    active_goals = [g for g in goals if g.get("pct", 0) < 100]
    return {
        "goals": {
            "items": goals[-8:],
            "active": len(active_goals),
            "avg": round(sum(g.get("pct", 0) for g in active_goals) / len(active_goals)) if active_goals else 0,
            "templates": G.GOAL_TEMPLATES,
        },
        "habits": {"items": habits[-8:], "active": len([h for h in habits if _num(h.get("streak", 0)) > 0])},
        "nutrition": {"items": nutrition[-8:]},
        "fitness": {"items": fitness[-8:]},
        "focus": {"items": focus[-8:]},
        "mental": {"items": mental[-8:]},
    }
