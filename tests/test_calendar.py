"""Calendar integration — verified without network or credentials."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from integrations import calendar_base as base
from integrations.google_calendar import _normalise_event as g_norm
from integrations.microsoft_calendar import _normalise_event as m_norm
from integrations.calendar_base import CalendarEvent, select_upcoming, is_stressful


def _dt(**kw):
    return datetime(2026, 7, 26, 9, 0, tzinfo=timezone.utc) + timedelta(**kw)


# ── normalisers ───────────────────────────────────────────────────────
class TestGoogleNormalise:
    def test_timed_event(self):
        ev = g_norm({
            "id": "g1", "summary": "Design review",
            "start": {"dateTime": "2026-07-26T09:00:00+02:00"},
            "end": {"dateTime": "2026-07-26T10:00:00+02:00"},
            "location": "Room 3", "htmlLink": "https://x",
        })
        assert ev.provider == "google"
        assert ev.title == "Design review"
        assert ev.all_day is False
        assert ev.location == "Room 3"
        assert ev.start_dt.tzinfo is not None

    def test_all_day_event(self):
        ev = g_norm({"id": "g2", "summary": "Holiday",
                     "start": {"date": "2026-07-26"}, "end": {"date": "2026-07-27"}})
        assert ev.all_day is True

    def test_missing_title_falls_back(self):
        ev = g_norm({"id": "g3", "start": {"date": "2026-07-26"}, "end": {"date": "2026-07-27"}})
        assert ev.title == "(no title)"


class TestMicrosoftNormalise:
    def test_timed_event(self):
        ev = m_norm({
            "id": "m1", "subject": "1:1",
            "start": {"dateTime": "2026-07-26T09:00:00.0000000", "timeZone": "UTC"},
            "end": {"dateTime": "2026-07-26T09:30:00.0000000", "timeZone": "UTC"},
            "isAllDay": False, "webLink": "https://y",
        })
        assert ev.provider == "microsoft"
        assert ev.title == "1:1"
        assert ev.all_day is False
        assert ev.start_dt.tzinfo is not None

    def test_all_day_event(self):
        ev = m_norm({"id": "m2", "subject": "OOO",
                     "start": {"date": "2026-07-26"}, "end": {"date": "2026-07-27"},
                     "isAllDay": True})
        assert ev.all_day is True


# ── selection / dedupe ────────────────────────────────────────────────
def _ev(pid, eid, start, end):
    return CalendarEvent(id=eid, provider=pid, title=eid,
                         start_iso=start.isoformat(), end_iso=end.isoformat(), all_day=False)


class TestSelectUpcoming:
    def test_drops_past_and_sorts(self):
        now = _dt()
        evs = [_ev("g", "b", _dt(hours=3), _dt(hours=4)),
               _ev("g", "a", _dt(hours=1), _dt(hours=2)),
               _ev("g", "past", _dt(hours=-5), _dt(hours=-4))]
        out = select_upcoming(evs, now, limit=5)
        assert [e.id for e in out] == ["a", "b"]

    def test_dedupes_across_providers_by_pair(self):
        now = _dt()
        evs = [_ev("g", "x", _dt(hours=1), _dt(hours=2)),
               _ev("g", "x", _dt(hours=1), _dt(hours=2))]
        assert len(select_upcoming(evs, now, 5)) == 1

    def test_respects_limit(self):
        now = _dt()
        evs = [_ev("g", str(i), _dt(hours=i), _dt(hours=i + 1)) for i in range(1, 8)]
        assert len(select_upcoming(evs, now, 3)) == 3


class TestStressful:
    def test_matches_hint(self):
        ev = _ev("g", "1", _dt(), _dt(hours=1)); ev.title = "Q3 Presentation"
        assert is_stressful(ev) is True

    def test_no_match(self):
        ev = _ev("g", "1", _dt(), _dt(hours=1)); ev.title = "Lunch with Sam"
        assert is_stressful(ev) is False


# ── token store tolerates missing / corrupt ───────────────────────────
class TestTokenStore:
    def test_round_trip(self, tmp_path, monkeypatch):
        monkeypatch.setattr(base, "TOKEN_FILE", tmp_path / "t.json")
        assert base.load_tokens() == {}
        base.set_token("google", {"access_token": "a", "refresh_token": "r", "expires_at": 1})
        assert base.get_token("google")["access_token"] == "a"
        base.clear_token("google")
        assert base.get_token("google") is None

    def test_corrupt_file_returns_empty(self, tmp_path, monkeypatch):
        f = tmp_path / "t.json"
        f.write_text("{not json", encoding="utf-8")
        monkeypatch.setattr(base, "TOKEN_FILE", f)
        assert base.load_tokens() == {}


# ── registry graceful degradation ─────────────────────────────────────
class TestRegistry:
    def test_unconfigured_when_env_missing(self, monkeypatch):
        from integrations.registry import get
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
        assert get("google").is_configured() is False

    def test_configured_when_env_present(self, monkeypatch):
        from integrations.registry import get
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "x")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "y")
        assert get("google").is_configured() is True
