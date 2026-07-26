"""Fetch upcoming events across connected providers, cached + deduped."""
from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import timedelta
from pathlib import Path

from storage import HERMES_DIR
from integrations.calendar_base import (
    CalendarError, CalendarEvent, Disconnected, now_utc, select_upcoming,
)
from integrations.registry import configured

CACHE_FILE = HERMES_DIR / "integrations" / "calendar_cache.json"
DEFAULT_TTL = 300  # seconds


def _cache_file() -> Path:
    return CACHE_FILE


def _load_cache() -> dict:
    p = _cache_file()
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save_cache(d: dict) -> None:
    p = _cache_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(tmp, p)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _from_cache(d: dict) -> list:
    out = []
    for ev in d.get("events", []):
        try:
            out.append(CalendarEvent(**ev))
        except TypeError:
            continue
    return out


def get_upcoming(limit: int = 5, ttl: int = DEFAULT_TTL, force: bool = False,
                 horizon_days: int = 14) -> tuple[list, dict]:
    """
    Returns (events, meta). meta = {fetched_at, per_provider: {name: ok|error}}.
    A provider that errors is skipped, never fatal. Fresh cache short-circuits.
    """
    cache = _load_cache()
    age = time.time() - cache.get("fetched_at", 0)
    if not force and cache.get("events") is not None and age < ttl:
        events = _from_cache(cache)
        return select_upcoming(events, now_utc(), limit), {
            "fetched_at": cache.get("fetched_at"), "cached": True,
            "per_provider": cache.get("per_provider", {}),
        }

    now = now_utc()
    time_max = now + timedelta(days=horizon_days)
    collected, per = [], {}
    for prov in configured():
        try:
            token = prov.live_token()
            collected.extend(prov.fetch_events(token, now, time_max))
            per[prov.name] = "ok"
        except Disconnected:
            per[prov.name] = "disconnected"
        except CalendarError:
            per[prov.name] = "error"

    _save_cache({"fetched_at": time.time(), "events": [e.to_dict() for e in collected],
                 "per_provider": per})
    return select_upcoming(collected, now, limit), {
        "fetched_at": time.time(), "cached": False, "per_provider": per,
    }
