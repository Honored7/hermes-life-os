"""
Hermes Life OS — Life dimensions.
Nine dimensions of a life, tracked gently. Built on demo/storage.py so it
shares one memory with the rest of Life OS (and the wizard can read it).
"""
from __future__ import annotations
from superapp.experience import store
import time
NOTE_DIMENSIONS = ['nutrition', 'fitness', 'mental', 'focus', 'habits', 'goals']

def _today() -> str:
    return time.strftime('%Y-%m-%d')

def get_hydration() -> dict:
    h = store.load_hydration()
    goal = h.get('goal', 8)
    if h.get('date') != _today():
        return {'today': 0, 'goal': goal}
    return {'today': h.get('today', 0), 'goal': goal}

def get_sleep() -> dict:
    sleep = store.load_sleep()
    today = next((s for s in reversed(sleep) if s.get('date') == _today()), None)
    recent = sleep[-7:]
    avg = round(sum((s.get('hours', 0) for s in recent)) / len(recent), 1) if recent else 0
    return {'today': today, 'avg_7d': avg}

def get_today_summary() -> dict:
    today = _today()
    recent = store.get_recent_memory(days=1)
    logged = {dim: any((e.get('type') == dim and str(e.get('date', '')).startswith(today) for e in recent)) for dim in NOTE_DIMENSIONS}
    return {'date': today, 'hydration': get_hydration(), 'sleep': get_sleep(), 'logged': logged}
