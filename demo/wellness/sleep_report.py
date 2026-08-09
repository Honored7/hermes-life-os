"""
Sleep — the keystone. A week of nights, hours and quality together,
and the gentle truth about how rest is shaping your days.
"""
from __future__ import annotations
from datetime import date, timedelta

TARGET = 7.5


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _load_sleep():
    try:
        from storage import load_sleep
        return load_sleep() or []
    except Exception:
        return []


def _read(avg_hours, avg_quality, recent):
    if not recent:
        return "No nights logged yet — the wizard already watches from your check-ins. Log a night and a rhythm forms."
    if avg_hours >= TARGET and avg_quality >= 6:
        return "You've been sleeping like someone who tends to themselves. Protect this."
    if avg_hours < 6:
        return "Running short on rest. Sleep is the keystone — even thirty more minutes changes the day."
    if avg_quality < 5:
        return "The hours are there but the rest isn't deep. A wind-down might help the nights land softer."
    return "Your rest is steadying. Keep the rhythm and the days will follow."


def sleep_report():
    nights = _load_sleep()
    week = []
    for i in range(6, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        e = next((x for x in nights if (x.get("date") or "") == d), None)
        week.append({
            "date": d,
            "hours": _num(e.get("hours")) if e else None,
            "quality": _num(e.get("quality")) if e else None,
        })
    logged = [x for x in nights if _num(x.get("hours")) > 0]
    recent = logged[-7:]
    avg_hours = round(sum(_num(x.get("hours")) for x in recent) / len(recent), 1) if recent else 0
    avg_quality = round(sum(_num(x.get("quality")) for x in recent) / len(recent), 1) if recent else 0
    good_week = sum(1 for w in week if (w["hours"] or 0) >= TARGET)

    insight = None
    try:
        from wellness.vitals import detect_sleep_mood_pattern
        insight = detect_sleep_mood_pattern()
    except Exception:
        insight = None

    return {
        "week": week,
        "recent": recent,
        "avg_hours": avg_hours,
        "avg_quality": avg_quality,
        "nights_logged": len(logged),
        "good_week": good_week,
        "target": TARGET,
        "mood_insight": insight,
        "read": _read(avg_hours, avg_quality, recent),
    }


def delete_sleep(d):
    from storage import load_sleep, save_sleep
    nights = load_sleep() or []
    kept = [x for x in nights if (x.get("date") or "") != d]
    if len(kept) == len(nights):
        return {"logged": False}
    save_sleep(kept)
    return {"logged": True}
