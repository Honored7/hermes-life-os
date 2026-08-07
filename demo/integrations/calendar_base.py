"""
Calendar integration — shared foundation.

One contract (CalendarProvider) + one normalised model (CalendarEvent) so
Google and Microsoft collapse into a single path downstream. Stdlib-only
HTTP (urllib) to avoid extra install-failure surface. Tokens persist with
their refresh token + expiry; the store tolerates a missing or corrupt file
by returning empty rather than throwing.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from storage import HERMES_DIR

# ── exceptions ────────────────────────────────────────────────────────
class CalendarError(RuntimeError):
    """Transient / provider error. Sync skips the provider and continues."""

class NotConfigured(CalendarError):
    """The provider's client credentials are absent from the environment."""

class Disconnected(CalendarError):
    """No token, or the refresh token was revoked. The UI should offer Connect."""


# ── normalised event ──────────────────────────────────────────────────
@dataclass
class CalendarEvent:
    id: str
    provider: str
    title: str
    start_iso: str          # aware ISO for the start instant
    end_iso: str            # aware ISO for the end instant
    all_day: bool
    location: str = ""
    html_link: str = ""

    @property
    def start_dt(self) -> datetime:
        return _parse(self.start_iso)

    @property
    def end_dt(self) -> datetime:
        return _parse(self.end_iso)

    def to_dict(self) -> dict:
        return asdict(self)


def _parse(iso: str) -> datetime:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── tiny stdlib HTTP ──────────────────────────────────────────────────
def http_get_json(url: str, headers: Optional[dict] = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise CalendarError(f"GET {url} -> {e.code}") from e
    except urllib.error.URLError as e:
        raise CalendarError(f"GET {url} failed: {e.reason}") from e


def http_post_form(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        payload = e.read().decode("utf-8", "ignore")
        # surface the provider's error code so refresh logic can detect revocation
        raise CalendarError(f"POST {url} -> {e.code}: {payload[:200]}") from e
    except urllib.error.URLError as e:
        raise CalendarError(f"POST {url} failed: {e.reason}") from e


# ── token store (atomic, corruption-tolerant) ─────────────────────────
TOKEN_FILE = HERMES_DIR / "integrations" / "calendar_tokens.json"


def _token_file() -> Path:
    return TOKEN_FILE


def load_tokens() -> dict:
    p = _token_file()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_tokens(data: dict) -> None:
    p = _token_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, p)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def get_token(provider: str) -> Optional[dict]:
    return load_tokens().get(provider)


def set_token(provider: str, token: dict) -> None:
    data = load_tokens()
    data[provider] = token
    save_tokens(data)


def clear_token(provider: str) -> None:
    data = load_tokens()
    data.pop(provider, None)
    save_tokens(data)


def is_expired(token: dict) -> bool:
    exp = token.get("expires_at", 0)
    return time.time() >= (exp - 60)


# ── provider interface ────────────────────────────────────────────────
class CalendarProvider:
    name: str = ""

    def is_configured(self) -> bool:  # pragma: no cover - overridden
        raise NotImplementedError

    def redirect_uri(self) -> str:  # pragma: no cover - overridden
        raise NotImplementedError

    def auth_url(self, state: str) -> str:  # pragma: no cover - overridden
        raise NotImplementedError

    def exchange_code(self, code: str) -> dict:  # pragma: no cover - overridden
        raise NotImplementedError

    def refresh(self, token: dict) -> dict:  # pragma: no cover - overridden
        raise NotImplementedError

    def account_label(self, token: dict) -> str:  # pragma: no cover - overridden
        raise NotImplementedError

    def fetch_events(self, token: dict, time_min: datetime, time_max: datetime) -> list:  # pragma: no cover
        raise NotImplementedError

    # convenience: a fresh, non-expired token or raise Disconnected
    def live_token(self) -> dict:
        token = get_token(self.name)
        if not token:
            raise Disconnected(f"{self.name} not connected")
        if not is_expired(token):
            return token
        try:
            refreshed = self.refresh(token)
        except CalendarError as e:
            if "invalid_grant" in str(e).lower() or "400" in str(e) or "401" in str(e):
                clear_token(self.name)
                raise Disconnected(f"{self.name} token revoked") from e
            raise
        # preserve metadata across refresh
        refreshed.setdefault("account_label", token.get("account_label", ""))
        refreshed.setdefault("connected_at", token.get("connected_at", time.time()))
        set_token(self.name, refreshed)
        return refreshed


# ── pure selection logic (tested without network) ─────────────────────
def select_upcoming(events: list, now: datetime, limit: int = 5) -> list:
    """Dedupe by (provider, id), drop the past, sort soonest-first, cap."""
    seen, kept = set(), []
    for ev in events:
        key = (ev.provider, ev.id)
        if key in seen:
            continue
        seen.add(key)
        if ev.end_dt >= now:
            kept.append(ev)
    kept.sort(key=lambda e: e.start_dt)
    return kept[:limit]


_STRESS_HINTS = (
    "presentation", "deadline", "interview", "review", "demo",
    "exam", "pitch", "defense", "defence", "performance", "hearing",
)


def is_stressful(event: CalendarEvent) -> bool:
    title = (event.title or "").lower()
    return any(h in title for h in _STRESS_HINTS)
