from __future__ import annotations
from datetime import date, timedelta
from wellness.insights import mood_trend


def _row(days_ago, state, sev):
    d = (date.today() - timedelta(days=days_ago)).isoformat()
    return {"type": "mood", "state": state, "severity": sev, "date": d, "timestamp": d + "T08:00:00Z"}


def test_empty_is_honest(monkeypatch):
    monkeypatch.setattr("wellness.insights.get_recent_memory", lambda days=21: [])
    t = mood_trend()
    assert t["series"] == []
    assert t["direction"] == "none"
    assert t["delta"] is None
    assert "still clearing" in t["verdict"]


def test_warming_shift(monkeypatch):
    rows = (
        [_row(d, "stressed", 8) for d in range(7, 13)]   # last week: cool
        + [_row(d, "good", 4) for d in range(0, 6)]      # this week: warm
    )
    monkeypatch.setattr("wellness.insights.get_recent_memory", lambda days=21: rows)
    t = mood_trend()
    assert t["direction"] == "warmer"
    assert t["this_predominant"] == "good"
    assert t["last_predominant"] == "stressed"
    assert "warmed" in t["verdict"]


def test_cooling_shift(monkeypatch):
    rows = (
        [_row(d, "calm" if False else "neutral", 3) for d in range(7, 13)]
        + [_row(d, "sad", 8) for d in range(0, 6)]
    )
    monkeypatch.setattr("wellness.insights.get_recent_memory", lambda days=21: rows)
    t = mood_trend()
    assert t["direction"] == "cooler"
    assert "cooler" in t["verdict"]


def test_holding_when_unchanged(monkeypatch):
    rows = [_row(d, "neutral", 4) for d in range(0, 13)]
    monkeypatch.setattr("wellness.insights.get_recent_memory", lambda days=21: rows)
    t = mood_trend()
    assert t["direction"] == "holding"


def test_series_one_point_per_day_averaged(monkeypatch):
    d0 = date.today().isoformat()
    rows = [
        {"type": "mood", "state": "stressed", "severity": 6, "date": d0, "timestamp": d0 + "T08:00:00Z"},
        {"type": "mood", "state": "stressed", "severity": 8, "date": d0, "timestamp": d0 + "T20:00:00Z"},
    ]
    monkeypatch.setattr("wellness.insights.get_recent_memory", lambda days=21: rows)
    t = mood_trend()
    assert len(t["series"]) == 1
    assert t["series"][0]["severity"] == 7.0
