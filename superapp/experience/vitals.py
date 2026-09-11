"""
Motif "eyes" — no wearable required.

The companion's sight comes from what you share effortlessly over time.
Sleep is the keystone signal that needs no hardware: log a few nights and
Motif learns your rhythm, notices a short-sleep streak, and — only once
there is enough paired sleep+mood data to support it — connects short
nights to heavier days. Every figure is read from real logs; nothing is
invented, and a pattern is claimed only when the data can carry it.
"""
from __future__ import annotations
from superapp.experience import store
LOW_SLEEP = 6.0
MIN_PAIRS = 3
_POSITIVE = {'good', 'neutral'}

def _sleep_logs() -> list:
    try:
        logs = store.load_sleep()
    except Exception:
        logs = []
    out = []
    for entry in logs:
        try:
            hours = float(entry.get('hours'))
        except (TypeError, ValueError):
            continue
        out.append({'date': entry.get('date', ''), 'hours': hours, 'quality': entry.get('quality')})
    return sorted(out, key=lambda x: x['date'])

def _day_weight(state: str, severity) -> float:
    """Higher = a heavier day. Intense joy/calm counts as light, not heavy."""
    sev = float(severity)
    return -sev if state in _POSITIVE else sev

def _mood_weight_by_date() -> dict:
    out: dict = {}
    try:
        entries = store.get_recent_memory(days=30)
    except Exception:
        entries = []
    for e in entries:
        if e.get('type') != 'mood':
            continue
        date = e.get('date') or str(e.get('timestamp', ''))[:10]
        if not date or e.get('severity') is None:
            continue
        try:
            out[date] = _day_weight(e.get('state', ''), e.get('severity'))
        except (TypeError, ValueError):
            continue
    return out

def sleep_summary() -> dict:
    logs = _sleep_logs()
    if not logs:
        return {'count': 0, 'avg_hours': None, 'last_hours': None, 'series': [], 'poor_streak': 0}
    hours = [night['hours'] for night in logs]
    last7 = hours[-7:]
    streak = 0
    for h in reversed(hours):
        if h < LOW_SLEEP:
            streak += 1
        else:
            break
    return {'count': len(logs), 'avg_hours': round(sum(last7) / len(last7), 1), 'last_hours': hours[-1], 'series': [{'date': night['date'], 'hours': night['hours']} for night in logs[-7:]], 'poor_streak': streak}

def detect_sleep_mood_pattern() -> str | None:
    logs = _sleep_logs()
    weights = _mood_weight_by_date()
    short_days, full_days = ([], [])
    for night in logs:
        w = weights.get(night['date'])
        if w is None:
            continue
        (short_days if night['hours'] < LOW_SLEEP else full_days).append(w)
    if len(short_days) < MIN_PAIRS or len(full_days) < MIN_PAIRS:
        return None
    short_avg = sum(short_days) / len(short_days)
    full_avg = sum(full_days) / len(full_days)
    diff = round(short_avg - full_avg, 1)
    if diff >= 1.0:
        return f'On nights under {int(LOW_SLEEP)} hours of sleep, your days have landed about {diff} points heavier than after a fuller night. Sleep looks like a real lever for you.'
    if diff <= -1.0:
        return "Interestingly, your heavier days haven't tracked with short sleep — something else may be driving them. Worth noticing together."
    return None

def rhythm_payload() -> dict:
    summary = sleep_summary()
    return {**summary, 'pattern': detect_sleep_mood_pattern()}

def vitals_note() -> str:
    """Guarded one-liner for the wizard's check-in context. Real figures only."""
    try:
        s = sleep_summary()
        if s['count'] == 0:
            return ''
        facts = []
        if s['poor_streak'] >= 2:
            facts.append(f"they've slept under {int(LOW_SLEEP)}h for {s['poor_streak']} nights running")
        elif s['avg_hours'] is not None and s['avg_hours'] < 6.5:
            facts.append(f"their sleep has averaged about {s['avg_hours']}h lately")
        if not facts:
            return ''
        pattern = detect_sleep_mood_pattern()
        extra = f' {pattern}' if pattern else ''
        return '\nVitals: ' + ', '.join(facts) + '.' + extra + " If it feels natural, you may gently connect how they're feeling to their sleep — but reference only these real figures; invent nothing."
    except Exception:
        return ''
