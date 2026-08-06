"""
The You room — the person, held.

moments(): achievements as warm one-liners earned from real data. No points,
no streaks that punish; only kept things, and one gentle invitation for the
first thing not yet kept.
export_all(): the whole of the person's data in one honest file.
wipe_all(): truly empties the journal. Bounded and shape-validated: it clears
the stores Motif owns outright (sleep, journal, vitals) and, for the base
memory journal, truncates ONLY top-level files that provably look like a
memory journal — never subdirs (so calendar tokens/caches stay safe).
"""
from __future__ import annotations

import json
import time

from storage import HERMES_DIR, load_sleep, save_sleep, get_recent_memory
from wellness.insights import get_wins
from wellness import journal, ingest
from integrations.calendar_base import load_tokens


def _counts() -> dict:
    try:
        mem = get_recent_memory(days=3650)
    except Exception:
        mem = []
    feel = sum(1 for e in mem if e.get("type") == "mood")
    steady = sum(1 for e in mem if e.get("type") == "preparation")
    try:
        wins_n = len(get_wins(limit=1000))
    except Exception:
        wins_n = 0
    try:
        nights = len(load_sleep())
    except Exception:
        nights = 0
    try:
        entries = journal.list_entries()
    except Exception:
        entries = []
    pages = sum(1 for e in entries if not e.get("is_dream"))
    dreams = sum(1 for e in entries if e.get("is_dream"))
    try:
        doors = [k for k, v in (load_tokens() or {}).items() if v]
    except Exception:
        doors = []
    return {"feel": feel, "wins": wins_n, "steady": steady, "nights": nights,
            "pages": pages, "dreams": dreams, "doors": doors}


def moments() -> dict:
    c = _counts()
    out = []

    def add(mid, icon, tone, text):
        out.append({"id": mid, "icon": icon, "tone": tone, "text": text})

    if c["feel"] >= 30:
        add("feel", "Smiley", "lantern", f"{c['feel']} check-ins — a month and more of naming your weather. The companion knows your sky.")
    elif c["feel"] >= 7:
        add("feel", "Smiley", "lantern", f"{c['feel']} times you named how you feel, instead of carrying it unnamed.")
    elif c["feel"] >= 1:
        add("feel", "Smiley", "lantern", f"You named how you feel — {c['feel']} time(s) so far. The first step in being known.")
    if c["wins"] >= 1:
        add("wins", "Trophy", "lantern", f"You wrote down {c['wins']} win(s), kept safe for the harder days.")
    if c["steady"] >= 1:
        add("steady", "Wind", "sage", f"You steadied yourself before {c['steady']} hard thing(s), on purpose.")
    if c["nights"] >= 7:
        add("nights", "MoonStars", "calm", f"{c['nights']} nights watched over — your rest, taken seriously.")
    elif c["nights"] >= 1:
        add("nights", "MoonStars", "calm", f"{c['nights']} night(s) logged — the beginning of a rhythm.")
    if c["pages"] >= 1:
        add("pages", "Feather", "lantern", f"{c['pages']} page(s) written from the heart.")
    if c["dreams"] >= 1:
        add("dreams", "Moon", "calm", f"{c['dreams']} dream(s) kept from fading.")
    if c["doors"]:
        add("door", "CalendarBlank", "sage", "You opened a door — your calendar now speaks to the wizard.")

    next_line = None
    if c["feel"] == 0:
        next_line = "Your first check-in is a one-tap thing on Today — name the weather, and the room starts filling."
    elif c["wins"] == 0:
        next_line = "Your first win is waiting to be written down. Even a small one counts."
    elif c["nights"] == 0:
        next_line = "Log a night of sleep, and the companion starts watching over your rest."
    elif c["pages"] == 0:
        next_line = "A blank page is waiting in your journal, patient as ever."

    return {"counts": c, "moments": out, "next": next_line}


def export_all() -> dict:
    try:
        mem = get_recent_memory(days=3650)
    except Exception:
        mem = []
    try:
        sleep = load_sleep()
    except Exception:
        sleep = []
    try:
        entries = journal.list_entries()
    except Exception:
        entries = []
    return {
        "app": "Motif",
        "exported_at": time.time(),
        "counts": _counts(),
        "memory": mem,
        "sleep": sleep,
        "journal": entries,
        "vitals": {
            "heart_rate": ingest._read("heart_rate.json"),
            "steps": ingest._read("steps.json"),
        },
    }


def _clear_memory_journal() -> list:
    """Truncate ONLY top-level files that provably look like the memory journal."""
    cleared = []
    try:
        base = HERMES_DIR
        for name in sorted(p.name for p in base.iterdir() if p.is_file()):
            if not (name.endswith(".json") or name.endswith(".jsonl")):
                continue
            p = base / name
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            sample = data[:5] if isinstance(data, list) else list(data.values())[:5]
            if sample and all(isinstance(e, dict) and "type" in e for e in sample):
                p.write_text("[]" if isinstance(data, list) else "{}", encoding="utf-8")
                cleared.append(name)
    except Exception:
        pass
    return cleared


def wipe_all() -> dict:
    cleared = []
    try:
        save_sleep([]); cleared.append("sleep")
    except Exception:
        pass
    try:
        journal.clear_entries(); cleared.append("journal")
    except Exception:
        pass
    try:
        ingest.clear_vitals(); cleared.append("vitals")
    except Exception:
        pass
    cleared += ["memory:" + n for n in _clear_memory_journal()]
    return {"cleared": cleared}
