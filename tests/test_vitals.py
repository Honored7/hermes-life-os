"""Motif eyes (sleep rhythm) — verified without network or credentials."""
from __future__ import annotations

from wellness import vitals


def _sleep(rows):
    return [{"date": d, "hours": h, "quality": q} for (d, h, q) in rows]


def _moods(rows):
    return [
        {"type": "mood", "date": d, "state": st, "severity": sev, "timestamp": d + "T08:00:00Z"}
        for (d, st, sev) in rows
    ]


class TestSleepSummary:
    def test_empty(self, monkeypatch):
        monkeypatch.setattr(vitals, "load_sleep", lambda: [])
        s = vitals.sleep_summary()
        assert s["count"] == 0
        assert s["avg_hours"] is None
        assert s["series"] == []
        assert s["poor_streak"] == 0

    def test_average_and_series(self, monkeypatch):
        rows = _sleep([("2026-07-20", 5, 4), ("2026-07-21", 8, 8), ("2026-07-22", 6.5, 6)])
        monkeypatch.setattr(vitals, "load_sleep", lambda: rows)
        s = vitals.sleep_summary()
        assert s["count"] == 3
        assert s["avg_hours"] == round((5 + 8 + 6.5) / 3, 1)
        assert s["last_hours"] == 6.5
        assert len(s["series"]) == 3

    def test_poor_streak_counts_recent_short_nights(self, monkeypatch):
        rows = _sleep([("2026-07-20", 8, 8), ("2026-07-21", 8, 8), ("2026-07-22", 5, 3), ("2026-07-23", 4, 2)])
        monkeypatch.setattr(vitals, "load_sleep", lambda: rows)
        assert vitals.sleep_summary()["poor_streak"] == 2

    def test_ignores_malformed_hours(self, monkeypatch):
        monkeypatch.setattr(vitals, "load_sleep", lambda: [{"date": "x", "hours": "oops"}, {"date": "y", "hours": 7}])
        s = vitals.sleep_summary()
        assert s["count"] == 1
        assert s["avg_hours"] == 7


class TestPattern:
    def test_needs_enough_paired_days(self, monkeypatch):
        monkeypatch.setattr(vitals, "load_sleep", lambda: _sleep([("2026-07-20", 5, 3), ("2026-07-21", 8, 8)]))
        monkeypatch.setattr(vitals, "get_recent_memory", lambda days=30: _moods([("2026-07-20", "stressed", 8), ("2026-07-21", "stressed", 3)]))
        assert vitals.detect_sleep_mood_pattern() is None

    def test_short_sleep_tracks_heavier_days(self, monkeypatch):
        sleep = _sleep([
            ("2026-07-20", 5, 3), ("2026-07-21", 5, 3), ("2026-07-22", 5, 3),
            ("2026-07-23", 8, 8), ("2026-07-24", 8, 8), ("2026-07-25", 8, 8),
        ])
        moods = _moods([
            ("2026-07-20", "stressed", 8), ("2026-07-21", "anxious", 7), ("2026-07-22", "sad", 9),
            ("2026-07-23", "stressed", 3), ("2026-07-24", "stressed", 4), ("2026-07-25", "stressed", 3),
        ])
        monkeypatch.setattr(vitals, "load_sleep", lambda: sleep)
        monkeypatch.setattr(vitals, "get_recent_memory", lambda days=30: moods)
        line = vitals.detect_sleep_mood_pattern()
        assert line is not None and "heavier" in line

    def test_positive_mood_counts_as_lighter(self):
        assert vitals._day_weight("good", 9) == -9
        assert vitals._day_weight("stressed", 9) == 9


class TestVitalsNote:
    def test_silent_without_data(self, monkeypatch):
        monkeypatch.setattr(vitals, "load_sleep", lambda: [])
        assert vitals.vitals_note() == ""

    def test_mentions_a_short_sleep_streak(self, monkeypatch):
        rows = _sleep([("2026-07-20", 8, 8), ("2026-07-21", 5, 3), ("2026-07-22", 5, 3)])
        monkeypatch.setattr(vitals, "load_sleep", lambda: rows)
        monkeypatch.setattr(vitals, "get_recent_memory", lambda days=30: [])
        note = vitals.vitals_note()
        assert "nights running" in note
        assert "invent nothing" in note


class TestRhythmPayload:
    def test_shape(self, monkeypatch):
        monkeypatch.setattr(vitals, "load_sleep", lambda: _sleep([("2026-07-22", 7, 7)]))
        monkeypatch.setattr(vitals, "get_recent_memory", lambda days=30: [])
        payload = vitals.rhythm_payload()
        assert "avg_hours" in payload and "series" in payload and "pattern" in payload
