"""
Ingest health data from wearables (Wear OS / Health Connect, and any future
source) into the stores the eyes read.

Sleep is the keystone: it flows into the SAME store the wizard's sleep
awareness uses, so a night measured by your watch is indistinguishable from
one you logged by hand — except it carries richer detail (deep / REM / light
/ awake) the eyes can grow into. Heart rate and steps are kept, bounded, for
the next layer of sight.
"""
from __future__ import annotations

import json

from storage import HERMES_DIR, load_sleep, save_sleep

_VITALS_DIR = HERMES_DIR / "integrations"


def _read(name: str) -> list:
    p = _VITALS_DIR / name
    if not p.exists():
        return []
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, list) else []
    except Exception:
        return []


def _write(name: str, data: list) -> None:
    _VITALS_DIR.mkdir(parents=True, exist_ok=True)
    (_VITALS_DIR / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def ingest_sleep(sessions: list) -> int:
    """Upsert wearable sleep into the sleep store — one entry per date."""
    by_date = {e.get("date"): e for e in load_sleep()}
    n = 0
    for s in sessions:
        date, hours = s.get("date"), s.get("hours")
        if not date or hours is None:
            continue
        entry = {
            "date": date,
            "hours": float(hours),
            "quality": s.get("quality"),
            "source": s.get("source", "wearable"),
        }
        for k in ("deep_min", "rem_min", "light_min", "awake_min"):
            if s.get(k) is not None:
                entry[k] = s[k]
        by_date[date] = entry
        n += 1
    save_sleep(list(by_date.values()))
    return n


def ingest_heart_rate(samples: list) -> int:
    store = _read("heart_rate.json")
    store.extend(samples)
    _write("heart_rate.json", store[-2000:])  # keep it bounded
    return len(samples)


def ingest_steps(days: list) -> int:
    by_date = {d.get("date"): d for d in _read("steps.json")}
    n = 0
    for d in days:
        if d.get("date") is not None and d.get("count") is not None:
            by_date[d["date"]] = {"date": d["date"], "count": int(d["count"]),
                                  "source": d.get("source", "wearable")}
            n += 1
    _write("steps.json", list(by_date.values()))
    return n


def ingest(payload: dict) -> dict:
    source = payload.get("source", "wearable")
    result = {}
    if payload.get("sleep"):
        for s in payload["sleep"]:
            s.setdefault("source", source)
        result["sleep"] = ingest_sleep(payload["sleep"])
    if payload.get("heart_rate"):
        result["heart_rate"] = ingest_heart_rate(payload["heart_rate"])
    if payload.get("steps"):
        result["steps"] = ingest_steps(payload["steps"])
    return result
