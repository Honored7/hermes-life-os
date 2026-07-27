from __future__ import annotations
from wellness.insights import mood_weather, STATES


def _m(rows):
    return [
        {"type": "mood", "state": st, "severity": sev, "date": d, "timestamp": d + "T08:00:00Z"}
        for (d, st, sev) in rows
    ]


def test_empty_is_honest(monkeypatch):
    monkeypatch.setattr("wellness.insights.get_recent_memory", lambda days=7: [])
    w = mood_weather()
    assert w["total"] == 0
    assert w["predominant"] is None
    assert w["temperature"] is None
    assert w["spread"] == 0


def test_predominant_and_spread(monkeypatch):
    rows = _m([
        ("2026-07-20", "stressed", 7), ("2026-07-21", "stressed", 8),
        ("2026-07-22", "stressed", 6), ("2026-07-23", "sad", 5),
        ("2026-07-24", "good", 3),
    ])
    monkeypatch.setattr("wellness.insights.get_recent_memory", lambda days=7: rows)
    w = mood_weather()
    assert w["total"] == 5
    assert w["predominant"] == "stressed"
    assert w["predominant_count"] == 3
    assert w["spread"] == 3
    assert w["temperature"] == round((7 + 8 + 6 + 5 + 3) / 5, 1)


def test_unknown_states_ignored(monkeypatch):
    rows = _m([("2026-07-20", "stressed", 4), ("2026-07-21", "not-a-mood", 9)])
    monkeypatch.setattr("wellness.insights.get_recent_memory", lambda days=7: rows)
    w = mood_weather()
    assert w["total"] == 1
    assert w["predominant"] == "stressed"
