"""
The journal — free-form entries the person writes from the heart.

Dream entries are theme-tagged on save by a small, deterministic reader we
call the wizard's read: instant, offline, and honest about being a heuristic.
(The local model can take over this tagging later with a one-line swap —
the no-internet rule is about the open web, never the companion on-device.)
Entries are the person's own words, stored on their device.
"""
from __future__ import annotations

import json
import os
import secrets
import tempfile
import time

from storage import HERMES_DIR

JOURNAL_DIR = HERMES_DIR / "journal"
ENTRIES_FILE = JOURNAL_DIR / "entries.json"

# the wizard's quiet read of a dream — keyword themes, never a diagnosis
DREAM_THEMES = {
    "water": ["water", "sea", "ocean", "river", "rain", "swim", "flood", "wave", "lake"],
    "movement": ["fly", "flying", "falling", "float", "running", "chase", "chased"],
    "anxiety": ["late", "lost", "miss", "teeth", "naked", "trapped", "exam", "test"],
    "hope": ["light", "sun", "warm", "gold", "bright", "garden", "bloom", "open"],
    "shadow": ["dark", "shadow", "night", "cold", "hide", "hidden", "fear"],
    "connection": ["mother", "father", "friend", "family", "love", "hold", "hug", "child"],
    "pressure": ["work", "boss", "deadline", "office", "school", "present", "speech"],
    "nostalgia": ["old", "home", "childhood", "remember", "past", "house", "young"],
}


def tag_dream(text: str) -> list:
    t = (text or "").lower()
    found = []
    for theme, words in DREAM_THEMES.items():
        if any(w in t for w in words):
            found.append(theme)
    return found[:4]


def _file() -> "object":
    return ENTRIES_FILE


def _load() -> list:
    p = _file()
    if not p.exists():
        return []
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, list) else []
    except Exception:
        return []


def _save(entries: list) -> None:
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    p = _file()
    fd, tmp = tempfile.mkstemp(dir=str(JOURNAL_DIR), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        os.replace(tmp, p)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# waking-page themes — the journal's quiet read of what your writing leans toward
THEMES = {
    "gratitude": ["grateful", "thankful", "thanks", "appreciate"],
    "work": ["work", "job", "boss", "deadline", "meeting", "project", "office"],
    "family": ["mother", "father", "mom", "dad", "sister", "brother", "family", "son", "daughter"],
    "connection": ["friend", "friends", "talked", "called", "together", "love"],
    "rest": ["sleep", "tired", "rest", "nap", "exhausted"],
    "anxiety": ["anxious", "anxiety", "worried", "worry", "nervous", "stress", "stressed"],
    "hope": ["hope", "hopeful", "excited", "looking forward", "plan"],
    "health": ["walk", "run", "gym", "exercise", "workout", "medicine", "headache", "paracetamol"],
    "low": ["sad", "down", "lonely", "alone", "cry"],
}


def tag_entry(text: str, is_dream: bool) -> list:
    t = (text or "").lower()
    tags = [k for k, ws in THEMES.items() if any(w in t for w in ws)]
    if is_dream:
        tags = tags + [x for x in tag_dream(text) if x not in tags]
    return tags[:5]


def add_entry(html: str, text: str, is_dream: bool) -> dict:
    entry = {
        "id": secrets.token_urlsafe(8),
        "html": (html or "")[:200000],
        "text": (text or "")[:50000],
        "is_dream": bool(is_dream),
        "tags": tag_entry(text, is_dream),
        "ts": time.time(),
    }
    entries = _load()
    entries.append(entry)
    _save(entries)
    return entry


def list_entries() -> list:
    return sorted(_load(), key=lambda e: e.get("ts", 0), reverse=True)


def delete_entry(entry_id: str) -> bool:
    entries = _load()
    kept = [e for e in entries if e.get("id") != entry_id]
    if len(kept) == len(entries):
        return False
    _save(kept)
    return True


def clear_entries() -> None:
    _save([])
