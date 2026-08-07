"""
Life dimension stats — read side.

Stands on the original Hermes Life OS data model (demo/storage.py loaders) so
every Life card shows REAL logs with proper units and the original weekly
report math, instead of one generic score.
"""
from __future__ import annotations
from datetime import date, timedelta

from storage import (
    load_nutrition, load_sleep, load_hydration, load_fitness,
    load_focus, load_mental, load_habits, load_goals, get_recent_memory,
)
from wellness import life


def _day(e) -> str:
    return str(e.get("date", ""))[:10]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _last7() -> list:
    return [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]


def _series(entries, value_fn, agg="sum"):
    out = []
    for d in _last7():
        vals = [v for v in (value_fn(e) for e in entries if _day(e) == d) if v is not None]
        if not vals:
            out.append({"date": d, "value": 0})
        else:
            v = sum(vals) if agg == "sum" else sum(vals) / len(vals)
            out.append({"date": d, "value": round(v, 1)})
    return out


def dimension_stats() -> dict:
    today = date.today().isoformat()
    week_cut = (date.today() - timedelta(days=7)).isoformat()

    hydration = life.get_hydration()
    sleep = life.get_sleep()
    nutrition = load_nutrition()
    fitness = load_fitness()
    focus = load_focus()
    mental = load_mental()
    habits = load_habits()
    goals = load_goals()
    hyd_mem = [e for e in get_recent_memory(days=7) if e.get("type") == "hydration"]

    meals_w = [m for m in nutrition if _day(m) >= week_cut]
    fit_w = [f for f in fitness if _day(f) >= week_cut]
    focus_w = [f for f in focus if _day(f) >= week_cut]
    stress_w = [m for m in mental if _day(m) >= week_cut and m.get("type") == "stress" and m.get("score")]
    med_w = [m for m in mental if _day(m) >= week_cut and m.get("type") == "meditation"]
    stress_today = [m for m in mental if _day(m) == today and m.get("type") == "stress" and m.get("score") is not None]

    active_habits = sorted([h for h in habits if _num(h.get("streak", 0)) > 0], key=lambda h: -_num(h.get("streak", 0)))
    active_goals = [g for g in goals if _num(g.get("progress", 0)) < 100]

    return {
        "hydration": {
            "unit": "glasses", "target": hydration.get("goal", 8), "lower_better": False,
            "today": hydration.get("today", 0),
            "series": _series(hyd_mem, lambda e: e.get("glasses")),
            "week": {"glasses_today": hydration.get("today", 0), "goal": hydration.get("goal", 8)},
            "list": [],
        },
        "sleep": {
            "unit": "h", "target": 7.5, "lower_better": False,
            "today": (sleep.get("today") or {}).get("hours"),
            "series": _series(load_sleep(), lambda e: e.get("hours")),
            "week": {"avg_hours": sleep.get("avg_7d", 0), "nights": len(load_sleep()[-7:])},
            "list": [],
        },
        "nutrition": {
            "unit": "kcal", "target": 2000, "lower_better": False,
            "today": sum(m.get("calories", 0) for m in nutrition if _day(m) == today),
            "series": _series(nutrition, lambda e: e.get("calories")),
            "week": {"meals": len(meals_w), "total_cal": sum(m.get("calories", 0) for m in meals_w)},
            "list": [m.get("food", "") for m in nutrition[-5:]],
        },
        "fitness": {
            "unit": "min", "target": 30, "lower_better": False,
            "today": sum(f.get("duration", 0) for f in fitness if _day(f) == today),
            "series": _series(fitness, lambda e: e.get("duration")),
            "week": {"workouts": len(fit_w), "types": sorted(set(f.get("type", "") for f in fit_w))},
            "list": [f.get("type", "") for f in fitness[-5:]],
        },
        "focus": {
            "unit": "min", "target": 90, "lower_better": False,
            "today": sum(f.get("duration", 0) for f in focus if _day(f) == today),
            "series": _series(focus, lambda e: e.get("duration")),
            "week": {"sessions": len(focus_w), "total_min": sum(f.get("duration", 0) for f in focus_w)},
            "list": [f.get("task", "") for f in focus[-5:]],
        },
        "mental": {
            "unit": "stress /10", "target": 4, "lower_better": True,
            "today": round(sum(m.get("score", 0) for m in stress_today) / len(stress_today), 1) if stress_today else None,
            "series": _series([m for m in mental if m.get("type") == "stress"], lambda e: e.get("score"), agg="avg"),
            "week": {"avg_stress": round(sum(m.get("score", 0) for m in stress_w) / len(stress_w), 1) if stress_w else 0,
                     "meditations": len(med_w)},
            "list": [],
        },
        "habits": {
            "unit": "day streak", "target": None, "lower_better": False,
            "today": active_habits[0].get("streak", 0) if active_habits else 0,
            "series": [],
            "week": {"active": len(active_habits)},
            "list": [[h.get("name", ""), h.get("streak", 0)] for h in active_habits[:5]],
        },
        "goals": {
            "unit": "%", "target": 100, "lower_better": False,
            "today": round(sum(_num(g.get("progress", 0)) for g in active_goals) / len(active_goals), 0) if active_goals else 0,
            "series": [],
            "week": {"active": len(active_goals)},
            "list": [[g.get("name", ""), _num(g.get("progress", 0))] for g in active_goals[:5]],
        },
    }


# ── write side: real logs, mirroring the original storage writes ──────
import time
from storage import (
    save_nutrition, save_fitness, save_focus, save_mental,
    save_habits, save_goals, write_memory,
)


def _now() -> str:
    return time.strftime("%Y-%m-%d")


def log_nutrition(food, calories=0, meal_time=""):
    from storage import load_nutrition
    n = load_nutrition()
    n.append({"date": _now(), "time": meal_time, "food": food, "calories": calories,
              "protein": 0, "carbs": 0, "fat": 0, "notes": ""})
    save_nutrition(n)
    write_memory({"type": "meal", "content": food, "calories": calories, "meal_time": meal_time, "date": _now()})
    return {"logged": True}


def log_fitness(workout_type, duration_min=0, intensity="medium"):
    from storage import load_fitness
    f = load_fitness()
    f.append({"date": _now(), "type": workout_type, "duration": duration_min,
              "intensity": intensity, "calories": 0, "notes": ""})
    save_fitness(f)
    write_memory({"type": "workout", "content": f"{workout_type} {duration_min}min", "duration": duration_min, "date": _now()})
    return {"logged": True}


def log_focus(task, duration_min=25, quality=7):
    from storage import load_focus
    f = load_focus()
    f.append({"date": _now(), "duration": duration_min, "task": task,
              "completed": True, "distractions": 0, "quality": quality})
    save_focus(f)
    write_memory({"type": "focus", "content": task, "duration": duration_min, "quality": quality, "date": _now()})
    return {"logged": True}


def log_stress(score, trigger=""):
    from storage import load_mental
    m = load_mental()
    m.append({"date": _now(), "type": "stress", "score": score, "trigger": trigger, "notes": ""})
    save_mental(m)
    write_memory({"type": "stress", "content": trigger or "stress", "score": score, "date": _now()})
    return {"logged": True}


def log_meditation(duration_min=10):
    from storage import load_mental
    m = load_mental()
    m.append({"date": _now(), "type": "meditation", "duration": duration_min, "notes": ""})
    save_mental(m)
    write_memory({"type": "meditation", "content": f"{duration_min}min meditation", "duration": duration_min, "date": _now()})
    return {"logged": True}


def log_gratitude(items):
    from storage import load_mental
    m = load_mental()
    m.append({"date": _now(), "type": "gratitude", "items": items, "notes": ""})
    save_mental(m)
    write_memory({"type": "gratitude", "content": ", ".join(items[:3]), "date": _now()})
    return {"logged": True}


def update_habit(habit_name, completed=True):
    from storage import load_habits
    habits = load_habits()
    found = False
    for h in habits:
        if h["name"].lower() == habit_name.lower():
            h["streak"] = h.get("streak", 0) + 1 if completed else 0
            h["last_done"] = _now()
            h["best_streak"] = max(h.get("best_streak", 0), h["streak"])
            found = True
            break
    if not found:
        habits.append({"name": habit_name, "streak": 1 if completed else 0,
                       "best_streak": 1 if completed else 0,
                       "last_done": _now() if completed else None, "created": _now()})
    save_habits(habits)
    return {"logged": True}


def update_goal(goal_name, progress=None, note=""):
    from storage import load_goals
    goals = load_goals()
    # normalize progress to a number (the frontend sends strings)
    if progress not in (None, ""):
        try:
            progress = float(progress)
        except (TypeError, ValueError):
            progress = None
    else:
        progress = None
    found = False
    for g in goals:
        if g["name"].lower() == goal_name.lower():
            if progress is not None:
                g["progress"] = progress
            g["last_updated"] = _now()
            g["last_note"] = note
            found = True
            break
    if not found:
        goals.append({"name": goal_name, "progress": progress or 0, "created": _now(),
                      "last_updated": _now(), "last_note": note})
    save_goals(goals)
    return {"logged": True}
