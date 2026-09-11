"""
Life dimension stats — read side.

Stands on the original Hermes Life OS data model (demo/storage.py loaders) so
every Life card shows REAL logs with proper units and the original weekly
report math, instead of one generic score.
"""
from __future__ import annotations
from superapp.experience import store
from datetime import date, timedelta
import time
from superapp.experience import life

def _day(e) -> str:
    return str(e.get('date', ''))[:10]

def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0

def _goals():
    try:
        from superapp.experience.store import load_goals
        return [g for g in load_goals() or [] if (g.get('name') or '').strip()]
    except Exception:
        return []

def _habits():
    try:
        from superapp.experience.store import load_habits
        return load_habits()
    except Exception:
        return []

def _last7() -> list:
    return [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]

def _series(entries, value_fn, agg='sum'):
    out = []
    for d in _last7():
        vals = [_num(v) for v in (value_fn(e) for e in entries if _day(e) == d) if v is not None]
        if not vals:
            out.append({'date': d, 'value': 0})
        else:
            v = sum(vals) if agg == 'sum' else sum(vals) / len(vals)
            out.append({'date': d, 'value': round(v, 1)})
    return out

def dimension_stats() -> dict:
    today = date.today().isoformat()
    week_cut = (date.today() - timedelta(days=7)).isoformat()
    hydration = life.get_hydration()
    sleep = life.get_sleep()
    nutrition = store.load_nutrition()
    fitness = store.load_fitness()
    focus = store.load_focus()
    mental = store.load_mental()
    habits = _habits()
    goals = _goals()
    hyd_mem = [e for e in store.get_recent_memory(days=7) if e.get('type') == 'hydration']
    meals_w = [m for m in nutrition if _day(m) >= week_cut]
    fit_w = [f for f in fitness if _day(f) >= week_cut]
    focus_w = [f for f in focus if _day(f) >= week_cut]
    stress_w = [m for m in mental if _day(m) >= week_cut and m.get('type') == 'stress' and m.get('score')]
    med_w = [m for m in mental if _day(m) >= week_cut and m.get('type') == 'meditation']
    stress_today = [m for m in mental if _day(m) == today and m.get('type') == 'stress' and (m.get('score') is not None)]
    active_habits = sorted([h for h in habits if _num(h.get('streak', 0)) > 0], key=lambda h: -_num(h.get('streak', 0)))
    active_goals = [g for g in goals if _num(g.get('progress', 0)) < 100]
    return {'hydration': {'unit': 'glasses', 'target': hydration.get('goal', 8), 'lower_better': False, 'today': hydration.get('today', 0), 'series': _series(hyd_mem, lambda e: _num(e.get('glasses'))), 'week': {'glasses_today': hydration.get('today', 0), 'goal': hydration.get('goal', 8)}, 'list': []}, 'sleep': {'unit': 'h', 'target': 7.5, 'lower_better': False, 'today': (sleep.get('today') or {}).get('hours'), 'series': _series(store.load_sleep(), lambda e: _num(e.get('hours'))), 'week': {'avg_hours': sleep.get('avg_7d', 0), 'nights': len(store.load_sleep()[-7:])}, 'list': []}, 'nutrition': {'unit': 'kcal', 'target': 2000, 'lower_better': False, 'today': sum((_num(m.get('calories')) for m in nutrition if _day(m) == today)), 'series': _series(nutrition, lambda e: _num(e.get('calories'))), 'week': {'meals': len(meals_w), 'total_cal': sum((_num(m.get('calories')) for m in meals_w))}, 'list': [m.get('food', '') for m in nutrition[-5:]]}, 'fitness': {'unit': 'min', 'target': 30, 'lower_better': False, 'today': sum((_num(f.get('duration')) for f in fitness if _day(f) == today)), 'series': _series(fitness, lambda e: _num(e.get('duration'))), 'week': {'workouts': len(fit_w), 'types': sorted(set((f.get('type', '') for f in fit_w)))}, 'list': [f.get('type', '') for f in fitness[-5:]]}, 'focus': {'unit': 'min', 'target': 90, 'lower_better': False, 'today': sum((_num(f.get('duration')) for f in focus if _day(f) == today)), 'series': _series(focus, lambda e: _num(e.get('duration'))), 'week': {'sessions': len(focus_w), 'total_min': sum((_num(f.get('duration')) for f in focus_w))}, 'list': [f.get('task', '') for f in focus[-5:]]}, 'mental': {'unit': 'stress /10', 'target': 4, 'lower_better': True, 'today': round(sum((_num(m.get('score')) for m in stress_today)) / len(stress_today), 1) if stress_today else None, 'series': _series([m for m in mental if m.get('type') == 'stress'], lambda e: e.get('score'), agg='avg'), 'week': {'avg_stress': round(sum((_num(m.get('score')) for m in stress_w)) / len(stress_w), 1) if stress_w else 0, 'meditations': len(med_w)}, 'list': []}, 'habits': {'unit': 'day streak', 'target': None, 'lower_better': False, 'today': active_habits[0].get('streak', 0) if active_habits else 0, 'series': [], 'week': {'active': len(active_habits)}, 'list': [[h.get('name', ''), h.get('streak', 0)] for h in active_habits[:5]]}, 'goals': {'unit': '%', 'target': 100, 'lower_better': False, 'today': round(sum((_num(g.get('progress', 0)) for g in active_goals)) / len(active_goals), 0) if active_goals else 0, 'series': [], 'week': {'active': len(active_goals)}, 'list': [[g.get('name', ''), _num(g.get('progress', 0))] for g in active_goals[:5]]}}
