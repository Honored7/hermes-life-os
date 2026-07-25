"""
Hermes Life OS — Life dimensions.
Nine dimensions of a life, tracked gently. Built on demo/storage.py so it
shares one memory with the rest of Life OS (and the wizard can read it).
"""
from __future__ import annotations

import time

from storage import (
    load_hydration, save_hydration,
    load_sleep, save_sleep,
    write_memory, get_recent_memory,
)

NOTE_DIMENSIONS = ["nutrition", "fitness", "mental", "focus", "habits", "goals"]


def _today() -> str:
    return time.strftime("%Y-%m-%d")


# ── Hydration ─────────────────────────────────────────────────────────
def get_hydration() -> dict:
    h = load_hydration()
    goal = h.get("goal", 8)
    if h.get("date") != _today():
        return {"today": 0, "goal": goal}
    return {"today": h.get("today", 0), "goal": goal}


def add_water(glasses: int = 1) -> dict:
    h = load_hydration()
    goal = h.get("goal", 8)
    if h.get("date") != _today():
        h = {"date": _today(), "today": 0, "goal": goal, "log": []}
    h["today"] = h.get("today", 0) + glasses
    h.setdefault("log", []).append({"time": time.strftime("%H:%M"), "glasses": glasses})
    save_hydration(h)
    write_memory({
        "type": "hydration", "content": f"{glasses} glass of water",
        "glasses": h["today"], "date": _today(),
    })
    return {"today": h["today"], "goal": goal}


# ── Sleep ─────────────────────────────────────────────────────────────
def log_sleep(hours: float, quality: int) -> dict:
    sleep = [s for s in load_sleep() if s.get("date") != _today()]
    entry = {"date": _today(), "hours": hours, "quality": quality}
    sleep.append(entry)
    save_sleep(sleep)
    write_memory({
        "type": "sleep", "content": f"{hours}h sleep, quality {quality}/10",
        "hours": hours, "quality": quality, "date": _today(),
    })
    return entry


def get_sleep() -> dict:
    sleep = load_sleep()
    today = next((s for s in reversed(sleep) if s.get("date") == _today()), None)
    recent = sleep[-7:]
    avg = round(sum(s.get("hours", 0) for s in recent) / len(recent), 1) if recent else 0
    return {"today": today, "avg_7d": avg}


# ── Generic note dimensions ───────────────────────────────────────────
def log_generic(dimension: str, note: str) -> dict:
    write_memory({"type": dimension, "content": note, "date": _today()})
    return {"dimension": dimension, "logged": True}


# ── Today's picture ───────────────────────────────────────────────────
def get_today_summary() -> dict:
    today = _today()
    recent = get_recent_memory(days=1)
    logged = {
        dim: any(
            e.get("type") == dim and str(e.get("date", "")).startswith(today)
            for e in recent
        )
        for dim in NOTE_DIMENSIONS
    }
    return {
        "date": today,
        "hydration": get_hydration(),
        "sleep": get_sleep(),
        "logged": logged,
    }
