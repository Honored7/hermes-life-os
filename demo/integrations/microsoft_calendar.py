"""Microsoft Graph (Outlook) adapter — conforms to CalendarProvider."""
from __future__ import annotations

import os
import urllib.parse
from datetime import datetime, timezone

from integrations.calendar_base import (
    CalendarEvent, CalendarProvider, NotConfigured, http_get_json, http_post_form,
)

_TENANT = "common"  # personal Microsoft accounts + work/school
_AUTH = f"https://login.microsoftonline.com/{_TENANT}/oauth2/v2.0/authorize"
_TOKEN = f"https://login.microsoftonline.com/{_TENANT}/oauth2/v2.0/token"
_VIEW = "https://graph.microsoft.com/v1.0/me/calendarView"
_ME = "https://graph.microsoft.com/v1.0/me"
_SCOPE = "Calendars.Read offline_access User.Read"


def _public_base() -> str:
    return os.environ.get("MOTIF_PUBLIC_URL", "http://localhost:8000").rstrip("/")


def _parse_when(when: dict) -> tuple[str, bool]:
    if when.get("dateTime"):
        tz = when.get("timeZone") or "UTC"
        iso = when["dateTime"]
        try:
            from zoneinfo import ZoneInfo
            from datetime import datetime as _dt
            naive = _dt.fromisoformat(iso.split(".")[0])
            aware = naive.replace(tzinfo=ZoneInfo(tz)).astimezone(ZoneInfo("UTC"))
            return aware.isoformat(), False
        except Exception:
            return (iso if iso.endswith(("Z", "+00:00")) or "+" in iso[10:] else iso + "+00:00"), False
    day = when.get("date", "")
    return f"{day}T00:00:00+00:00", True


def _normalise_event(raw: dict, provider: str = "microsoft") -> CalendarEvent:
    start_raw, all_day = _parse_when(raw.get("start", {}))
    end_raw, _ = _parse_when(raw.get("end", {}))
    loc = raw.get("location") or {}
    return CalendarEvent(
        id=str(raw.get("id", "")),
        provider=provider,
        title=raw.get("subject") or "(no title)",
        start_iso=start_raw,
        end_iso=end_raw,
        all_day=bool(raw.get("isAllDay")) or all_day,
        location=loc.get("displayName", "") or "",
        html_link=raw.get("webLink", "") or "",
    )


class MicrosoftCalendar(CalendarProvider):
    name = "microsoft"

    def is_configured(self) -> bool:
        return bool(os.environ.get("MICROSOFT_CLIENT_ID") and os.environ.get("MICROSOFT_CLIENT_SECRET"))

    def redirect_uri(self) -> str:
        return f"{_public_base()}/api/v1/integrations/calendar/microsoft/callback"

    def auth_url(self, state: str) -> str:
        if not self.is_configured():
            raise NotConfigured("Microsoft client credentials not set")
        params = {
            "client_id": os.environ["MICROSOFT_CLIENT_ID"],
            "redirect_uri": self.redirect_uri(),
            "response_type": "code",
            "response_mode": "query",
            "scope": _SCOPE,
            "state": state,
        }
        return f"{_AUTH}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str) -> dict:
        if not self.is_configured():
            raise NotConfigured("Microsoft client credentials not set")
        resp = http_post_form(_TOKEN, {
            "client_id": os.environ["MICROSOFT_CLIENT_ID"],
            "client_secret": os.environ["MICROSOFT_CLIENT_SECRET"],
            "code": code,
            "redirect_uri": self.redirect_uri(),
            "grant_type": "authorization_code",
            "scope": _SCOPE,
        })
        return _shape_token(resp)

    def refresh(self, token: dict) -> dict:
        resp = http_post_form(_TOKEN, {
            "client_id": os.environ["MICROSOFT_CLIENT_ID"],
            "client_secret": os.environ["MICROSOFT_CLIENT_SECRET"],
            "refresh_token": token["refresh_token"],
            "grant_type": "refresh_token",
            "scope": _SCOPE,
        })
        out = _shape_token(resp)
        out.setdefault("refresh_token", token.get("refresh_token"))
        return out

    def account_label(self, token: dict) -> str:
        try:
            me = http_get_json(_ME, {"Authorization": f"Bearer {token['access_token']}"})
            return me.get("mail") or me.get("userPrincipalName") or me.get("displayName") or "Microsoft"
        except Exception:
            return "Microsoft"

    def fetch_events(self, token: dict, time_min: datetime, time_max: datetime) -> list:
        # calendarView returns exactly the events occurring in [time_min, time_max]
        # and expands recurring instances. /me/events + $top would return the oldest
        # 100 events (all past, on a calendar with history) and filter to nothing.
        qs = urllib.parse.urlencode({
            "startDateTime": time_min.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endDateTime": time_max.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "$select": "id,subject,start,end,isAllDay,location,webLink",
            "$top": "100",
            "$orderby": "start/dateTime",
        })
        data = http_get_json(f"{_VIEW}?{qs}", {"Authorization": f"Bearer {token['access_token']}"})
        return [_normalise_event(it) for it in data.get("value", [])]


def _shape_token(resp: dict) -> dict:
    import time
    return {
        "access_token": resp["access_token"],
        "refresh_token": resp.get("refresh_token", ""),
        "expires_at": time.time() + int(resp.get("expires_in", 3600)),
        "token_type": resp.get("token_type", "Bearer"),
        "scope": resp.get("scope", _SCOPE),
    }
