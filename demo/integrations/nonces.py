"""One-time OAuth state nonces, persisted with expiry."""
from __future__ import annotations

import json
import os
import secrets
import tempfile
import time
from pathlib import Path

from storage import HERMES_DIR

NONCE_FILE = HERMES_DIR / "integrations" / "calendar_nonces.json"
TTL = 600


def _file() -> Path:
    return NONCE_FILE


def _load() -> dict:
    p = _file()
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save(d: dict) -> None:
    p = _file()
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(tmp, p)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def create(redirect: str) -> str:
    d = _load()
    nonce = secrets.token_urlsafe(24)
    d[nonce] = {"redirect": redirect, "exp": time.time() + TTL}
    _save(d)
    return nonce


def consume(nonce: str) -> str | None:
    """Return the stored redirect if valid, else None. Always deletes the nonce."""
    d = _load()
    entry = d.pop(nonce, None)
    _save(d)
    if not entry or entry.get("exp", 0) < time.time():
        return None
    return entry.get("redirect")
