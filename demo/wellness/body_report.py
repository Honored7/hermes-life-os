"""
Hydration & Nutrition — the body's daily rhythms.

Hydration: a row of droplets toward your goal, a week of watered days.
Nutrition: today's plate (meals + macro split), a gentle week of eating rhythm.

Never guilt. The companion notices; it doesn't scold.
"""
from __future__ import annotations
import time
from datetime import date, timedelta


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _today():
    return date.today().isoformat()


def _last7():
    return [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]


# ── Hydration ─────────────────────────────────────────────────────────
def _hydration_read(today, goal):
    if today >= goal:
        return "Fully watered today. Your body thanks you in ways you won't notice — that's the point."
    if today == 0:
        return "A fresh, dry page. The first glass is the kindest one."
    left = goal - today
    return f"{today} of {goal} — {left} more and the day is watered."


def hydration_report():
    from wellness import life
    from storage import get_recent_memory
    h = life.get_hydration()
    goal = int(_num(h.get("goal")) or 8)
    today = int(_num(h.get("today")))
    by_day = {}
    for e in (get_recent_memory(days=7) or []):
        if e.get("type") != "hydration":
            continue
        d = str(e.get("date") or "")
        by_day[d] = max(by_day.get(d, 0), _num(e.get("glasses")))
    week = [{"date": d, "glasses": by_day.get(d)} for d in _last7()]
    good_week = sum(1 for w in week if (w["glasses"] or 0) >= goal)
    return {"today": today, "goal": goal, "week": week, "good_week": good_week,
            "read": _hydration_read(today, goal)}


def set_hydration(n):
    from storage import load_hydration, save_hydration, write_memory
    h = load_hydration()
    t = _today()
    if h.get("date") != t:
        h = {"date": t, "today": 0, "goal": h.get("goal", 8), "log": []}
    n = max(0, int(_num(n)))
    h["today"] = n
    h.setdefault("log", []).append({"time": time.strftime("%H:%M"), "glasses": n})
    save_hydration(h)
    write_memory({"type": "hydration", "content": f"{n} glasses of water", "glasses": n, "date": t})
    return {"today": n, "goal": h.get("goal", 8)}


# ── Nutrition ─────────────────────────────────────────────────────────
def _nutrition_read(meals, cal):
    if meals == 0:
        return "Nothing logged yet today. The body keeps its own quiet tally — feed it kindly."
    if meals >= 3:
        return "Three meals and counting — your body likes this rhythm."
    return f"{meals} meal(s) so far. A body runs on rhythm more than perfection."


def nutrition_report():
    from storage import load_nutrition
    meals = load_nutrition() or []
    t = _today()
    recent = []
    for i, m in enumerate(meals):
        if (m.get("date") or "") == t:
            recent.append(dict(m, _idx=i))
    cal = sum(_num(m.get("calories")) for m in recent)
    protein = sum(_num(m.get("protein")) for m in recent)
    carbs = sum(_num(m.get("carbs")) for m in recent)
    fat = sum(_num(m.get("fat")) for m in recent)
    week = []
    for d in _last7():
        dm = [m for m in meals if (m.get("date") or "") == d]
        week.append({"date": d, "cal": sum(_num(m.get("calories")) for m in dm), "meals": len(dm)})
    logged_days = [w for w in week if w["meals"] > 0]
    avg_cal = round(sum(w["cal"] for w in logged_days) / len(logged_days)) if logged_days else 0
    return {
        "today": {"meals": len(recent), "cal": cal, "protein": protein, "carbs": carbs, "fat": fat},
        "recent": recent, "week": week, "avg_cal": avg_cal,
        "read": _nutrition_read(len(recent), cal),
    }


def delete_meal(idx):
    from storage import load_nutrition, save_nutrition
    meals = load_nutrition() or []
    idx = int(_num(idx))
    if 0 <= idx < len(meals):
        meals.pop(idx)
        save_nutrition(meals)
        return {"logged": True}
    return {"logged": False}


# ── Fitness ───────────────────────────────────────────────────────────
def _fitness_read(active_days, total_min):
    if active_days == 0:
        return "No movement logged this week. The body doesn't ask for much — just to be listened to."
    if active_days >= 3:
        return f"{active_days} active days — your body is being listened to. Keep the rhythm."
    return f"{active_days} active day(s) this week. Even a walk counts as listening."


def fitness_report():
    from storage import load_fitness
    w = load_fitness() or []
    week = []
    for d in _last7():
        dw = [x for x in w if (x.get("date") or "") == d]
        week.append({"date": d, "min": sum(_num(x.get("duration")) for x in dw), "workouts": len(dw)})
    active_days = sum(1 for x in week if x["workouts"] > 0)
    total_min = int(sum(x["min"] for x in week))
    types = sorted({x.get("type") for x in w if x.get("type")})[-5:]
    recent = [dict(x, _idx=i) for i, x in enumerate(w)][-6:]
    return {"week": week, "active_days": active_days, "total_min": total_min,
            "types": types, "recent": recent, "read": _fitness_read(active_days, total_min)}


# ── Focus ─────────────────────────────────────────────────────────────
def _focus_read(total_min, sessions):
    if sessions == 0:
        return "No deep work logged this week. Focus returns when you make a little quiet for it."
    if total_min >= 120:
        return f"{total_min} minutes of deep work — that's real, protected attention."
    return f"{total_min} minutes of focus this week. Small quiet blocks add up."


def focus_report():
    from storage import load_focus
    f = load_focus() or []
    week = []
    for d in _last7():
        df = [x for x in f if (x.get("date") or "") == d]
        week.append({"date": d, "min": sum(_num(x.get("duration")) for x in df), "sessions": len(df)})
    total_min = int(sum(x["min"] for x in week))
    sessions = sum(x["sessions"] for x in week)
    avg = round(total_min / sessions) if sessions else 0
    recent = [dict(x, _idx=i) for i, x in enumerate(f)][-6:]
    return {"week": week, "total_min": total_min, "sessions": sessions, "avg": avg,
            "recent": recent, "read": _focus_read(total_min, sessions)}


# ── Mental ────────────────────────────────────────────────────────────
def _mental_read(avg_stress, med_sessions):
    if avg_stress is None and med_sessions == 0:
        return "A quiet week for the mind. Name a feeling when it arrives — it gets smaller when named."
    if avg_stress is not None and avg_stress >= 6:
        return "The mind has been carrying a lot this week. Be gentle with it — and with yourself."
    if med_sessions > 0:
        return f"{med_sessions} moment(s) of stillness this week. The mind notices those."
    return "The mind is steady. A little stillness now and then keeps it that way."


def mental_report():
    from storage import load_mental
    m = load_mental() or []
    ws = (date.today() - timedelta(days=6)).isoformat()
    week = []
    for d in _last7():
        ds = [x for x in m if (x.get("date") or "") == d and x.get("type") == "stress"]
        week.append({"date": d, "score": round(sum(_num(x.get("score")) for x in ds) / len(ds), 1) if ds else None})
    stress_week = [x for x in m if (x.get("date") or "") >= ws and x.get("type") == "stress"]
    avg_stress = round(sum(_num(x.get("score")) for x in stress_week) / len(stress_week), 1) if stress_week else None
    med_week = [x for x in m if (x.get("date") or "") >= ws and x.get("type") == "meditation"]
    grat_week = [x for x in m if (x.get("date") or "") >= ws and x.get("type") == "gratitude"]
    recent = [dict(x, _idx=i) for i, x in enumerate(m)][-6:]
    return {"week": week, "avg_stress": avg_stress, "med_sessions": len(med_week),
            "med_min": int(sum(_num(x.get("duration")) for x in med_week)), "grat": len(grat_week),
            "recent": recent, "read": _mental_read(avg_stress, len(med_week))}


def delete_workout(idx):
    from storage import load_fitness, save_fitness
    w = load_fitness() or []
    idx = int(_num(idx))
    if 0 <= idx < len(w):
        w.pop(idx)
        save_fitness(w)
        return {"logged": True}
    return {"logged": False}


def delete_focus(idx):
    from storage import load_focus, save_focus
    f = load_focus() or []
    idx = int(_num(idx))
    if 0 <= idx < len(f):
        f.pop(idx)
        save_focus(f)
        return {"logged": True}
    return {"logged": False}


def delete_mental(idx):
    from storage import load_mental, save_mental
    m = load_mental() or []
    idx = int(_num(idx))
    if 0 <= idx < len(m):
        m.pop(idx)
        save_mental(m)
        return {"logged": True}
    return {"logged": False}
