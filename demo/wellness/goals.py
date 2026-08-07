"""
Goals that coach instead of ask.

A goal carries a target + unit and a *source* for its progress:
  - None           -> a count you move with a single "+1" tap
  - "habit:<name>" -> fed automatically each time that habit is marked done
  - "dim:<id>"     -> magical: computed from that dimension's real logs this week

The app does the %, the plain-English read, and the pace math. You just live.
Goals with only a legacy `progress` (no target) keep displaying that as their %.
"""
from __future__ import annotations
from datetime import date, timedelta


def _today():
    return date.today()


def _week_start():
    t = _today()
    return t - timedelta(days=t.weekday())


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


GOAL_TEMPLATES = [
    {"label": "Work out 3x this week", "name": "Work out 3x this week", "unit": "workouts", "target": 3, "source": "dim:fitness"},
    {"label": "Sleep 7h+, five nights", "name": "Sleep well five nights", "unit": "nights", "target": 5, "source": "dim:sleep", "unit_target": 7},
    {"label": "Hydrate five days", "name": "Hydrate five days", "unit": "days", "target": 5, "source": "dim:hydration", "unit_target": 8},
    {"label": "Read 5 books", "name": "Read 5 books", "unit": "books", "target": 5, "source": None},
]


def habit_hint_for(name, unit):
    n = (name or "").lower()
    u = (unit or "").lower()
    if "book" in n or "read" in n or u == "books":
        return "Read 20 minutes before bed"
    if "work" in n or "gym" in n or "fit" in n or "run" in n or u == "workouts":
        return "Lay out your kit the night before"
    if "water" in n or "hydrat" in n or u in ("glasses", "days"):
        return "Keep a bottle on your desk"
    if "sleep" in n or u == "nights":
        return "Screens off 30 minutes before bed"
    if "meditat" in n or "calm" in n or "mind" in n:
        return "Two mindful breaths at each doorway"
    return "Pick one small daily step and protect it"


def default_unit_target(dim):
    return {"hydration": 8, "sleep": 7, "fitness": 1}.get(dim, 1)


def _dim_count(dim, unit_target, ws):
    import storage
    if dim == "fitness":
        return sum(1 for f in (storage.load_fitness() or []) if (f.get("date") or "") >= ws)
    if dim == "sleep":
        return sum(1 for s in (storage.load_sleep() or [])
                   if (s.get("date") or "") >= ws and _num(s.get("hours")) >= unit_target)
    if dim == "hydration":
        by_day = {}
        for e in (storage.get_recent_memory(days=7) or []):
            if e.get("type") != "hydration":
                continue
            d = str(e.get("date") or "")
            if d < ws:
                continue
            by_day[d] = max(by_day.get(d, 0), _num(e.get("glasses")))
        return sum(1 for v in by_day.values() if v >= unit_target)
    return 0


def pace_note(goal, count, target):
    dl = goal.get("deadline")
    if not dl or not target:
        return None
    try:
        created = date.fromisoformat(str(goal.get("created") or _today().isoformat()))
        end = date.fromisoformat(str(dl))
    except ValueError:
        return None
    total_days = (end - created).days
    if total_days <= 0:
        return None
    elapsed = max(0, min(total_days, (_today() - created).days))
    expected = target * (elapsed / total_days)
    unit = goal.get("unit") or "steps"
    if count >= expected * 1.05:
        return "ahead of pace — quietly impressive"
    if count >= expected * 0.8:
        return "right on pace"
    per_week = (target - count) / max(1, (total_days - elapsed) / 7)
    return f"a little behind — about {per_week:.1f} {unit}/week catches you up"


def compute_goal(goal):
    steps = goal.get("steps") or []
    if steps:
        total = len(steps)
        done = sum(1 for st in steps if st.get("done"))
        next_step = next(({"name": st.get("name"), "index": i}
                          for i, st in enumerate(steps) if not st.get("done")), None)
        out = dict(goal)
        out.update({
            "count": done, "target": total,
            "pct": min(100, round(done / total * 100)) if total else 0,
            "unit": "steps",
            "steps": steps,
            "next_step": next_step,
            "pace": pace_note(goal, done, total),
            "habit_hint": goal.get("habit_hint") or habit_hint_for(goal.get("name"), "steps"),
        })
        return out
    target = _num(goal.get("target"))
    unit = goal.get("unit") or ""
    source = goal.get("source") or None
    ws = _week_start().isoformat()

    if source and source.startswith("dim:"):
        count = _dim_count(source[4:], _num(goal.get("unit_target")) or default_unit_target(source[4:]), ws)
    elif source and source.startswith("habit:"):
        from storage import load_habits
        h = next((x for x in (load_habits() or []) if x.get("name") == source[6:]), None)
        count = _num(h.get("total_done")) if h else _num(goal.get("count"))
    else:
        count = _num(goal.get("count"))

    if target:
        pct = min(100, round(count / target * 100))
    else:
        pct = min(100, round(_num(goal.get("progress"))))
        count = count or pct

    out = dict(goal)
    out.update({
        "count": count, "target": target, "pct": pct,
        "pace": pace_note(goal, count, target),
        "habit_hint": goal.get("habit_hint") or habit_hint_for(goal.get("name"), unit),
    })
    return out


def upsert_goal(fields):
    from storage import load_goals, save_goals
    goals = load_goals() or []
    name = (fields.get("name") or fields.get("goal_name") or "").strip()
    if not name:
        return {"logged": False}
    g = next((x for x in goals if (x.get("name") or "") == name), None)
    if g is None:
        g = {"name": name, "created": _today().isoformat()}
        goals.append(g)
    for k in ("target", "unit", "source", "deadline", "habit_hint", "count", "unit_target"):
        if fields.get(k) is not None:
            g[k] = fields[k]
    if fields.get("steps") is not None:
        raw = fields.get("steps")
        if isinstance(raw, str):
            names = [x.strip() for x in raw.splitlines() if x.strip()]
        elif isinstance(raw, list):
            names = [str(x).strip() for x in raw if str(x).strip()]
        else:
            names = []
        if names:
            g["steps"] = [{"name": n, "done": False} for n in names]
    g["last_updated"] = _today().isoformat()
    if fields.get("note"):
        g["last_note"] = fields["note"]
    save_goals(goals)
    return {"logged": True}


def increment_goal(name, by=1):
    from storage import load_goals, save_goals
    goals = load_goals() or []
    g = next((x for x in goals if (x.get("name") or "") == name), None)
    if g is None:
        return {"logged": False}
    g["count"] = _num(g.get("count")) + by
    g["last_updated"] = _today().isoformat()
    save_goals(goals)
    return {"logged": True}


def bump_habit_total(name):
    # history/streak/total_done are maintained by update_habit now
    return

def rename_goal(old_name, new_name):
    from storage import load_goals, save_goals
    new_name = (new_name or "").strip()
    if not new_name:
        return {"logged": False}
    goals = load_goals() or []
    g = next((x for x in goals if (x.get("name") or "") == old_name), None)
    if g is None:
        return {"logged": False}
    g["name"] = new_name
    g["last_updated"] = _today().isoformat()
    save_goals(goals)
    return {"logged": True}


def delete_goal(name):
    from storage import load_goals, save_goals
    goals = load_goals() or []
    kept = [x for x in goals if (x.get("name") or "") != name]
    if len(kept) == len(goals):
        return {"logged": False}
    save_goals(kept)
    return {"logged": True}


def add_goal_step(goal_name, step_name):
    from storage import load_goals, save_goals
    step_name = (step_name or "").strip()
    if not step_name:
        return {"logged": False}
    goals = load_goals() or []
    g = next((x for x in goals if (x.get("name") or "") == goal_name), None)
    if g is None:
        return {"logged": False}
    g.setdefault("steps", []).append({"name": step_name, "done": False})
    g["last_updated"] = _today().isoformat()
    save_goals(goals)
    return {"logged": True}


def set_goal_step(goal_name, index, done):
    from storage import load_goals, save_goals
    goals = load_goals() or []
    g = next((x for x in goals if (x.get("name") or "") == goal_name), None)
    if g is None:
        return {"logged": False}
    steps = g.get("steps") or []
    if 0 <= index < len(steps):
        steps[index]["done"] = bool(done)
        g["last_updated"] = _today().isoformat()
        save_goals(goals)
        return {"logged": True}
    return {"logged": False}
