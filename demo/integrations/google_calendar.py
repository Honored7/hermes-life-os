"""Google Calendar adapter — conforms to CalendarProvider."""
from __future__ import annotations

import os
import urllib.parse
from datetime import datetime

from integrations.calendar_base import (
    CalendarEvent, CalendarProvider, NotConfigured, http_get_json, http_post_form, now_utc,
)

_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN = "https://oauth2.googleapis.com/token"
_EVENTS = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
_ME = "https://www.googleapis.com/oauth2/v2/userinfo"
_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"


def _public_base() -> str:
    return os.environ.get("MOTIF_PUBLIC_URL", "http://localhost:8000").rstrip("/")


def _parse_when(when: dict, end: bool = False) -> tuple[str, bool]:
    if "dateTime" in when:
        return when["dateTime"], False
    # all-day: Google gives a date; end is exclusive, so keep as-is for display
    day = when.get("date", "")
    return f"{day}T00:00:00+00:00", True


def _normalise_event(raw: dict, provider: str = "google") -> CalendarEvent:
    start_raw, all_day = _parse_when(raw.get("start", {}))
    end_raw, _ = _parse_when(raw.get("end", {}), end=True)
    return CalendarEvent(
        id=str(raw.get("id", "")),
        provider=provider,
        title=raw.get("summary") or raw.get("description") or "(no title)",
        start_iso=start_raw,
        end_iso=end_raw,
        all_day=all_day,
        location=raw.get("location", "") or "",
        html_link=raw.get("htmlLink", "") or "",
    )


class GoogleCalendar(CalendarProvider):
    name = "google"

    def is_configured(self) -> bool:
        return bool(os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET"))

    def redirect_uri(self) -> str:
        return f"{_public_base()}/api/v1/integrations/calendar/google/callback"

    def auth_url(self, state: str) -> str:
        if not self.is_configured():
            raise NotConfigured("Google client credentials not set")
        params = {
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "redirect_uri": self.redirect_uri(),
            "response_type": "code",
            "scope": _SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{_AUTH}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str) -> dict:
        if not self.is_configured():
            raise NotConfigured("Google client credentials not set")
        import time
        resp = http_post_form(_TOKEN, {
            "code": code,
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "redirect_uri": self.redirect_uri(),
            "grant_type": "authorization_code",
        })
        return _shape_token(resp)

    def refresh(self, token: dict) -> dict:
        import time
        resp = http_post_form(_TOKEN, {
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "refresh_token": token["refresh_token"],
            "grant_type": "refresh_token",
        })
        out = _shape_token(resp)
        out.setdefault("refresh_token", token.get("refresh_token"))
        return out

    def account_label(self, token: dict) -> str:
        try:
            me = http_get_json(_ME, {"Authorization": f"Bearer {token['access_token']}"})
            return me.get("email") or me.get("name") or "Google"
        except Exception:
            return "Google"

    def fetch_events(self, token: dict, time_min: datetime, time_max: datetime) -> list:
        qs = urllib.parse.urlencode({
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": "100",
        })
        data = http_get_json(f"{_EVENTS}?{qs}", {"Authorization": f"Bearer {token['access_token']}"})
        return [_normalise_event(it) for it in data.get("items", [])]


def _shape_token(resp: dict) -> dict:
    import time
    return {
        "access_token": resp["access_token"],
        "refresh_token": resp.get("refresh_token", ""),
        "expires_at": time.time() + int(resp.get("expires_in", 3600)),
        "token_type": resp.get("token_type", "Bearer"),
        "scope": resp.get("scope", _SCOPE),
    }
