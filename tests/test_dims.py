from __future__ import annotations
from wellness import dims
from wellness import life_stats as LS


def test_records_reflect_created_goals(monkeypatch):
    fake = [
        {"name": "Read 12 books", "progress": 40},
        {"name": "Ship the app", "progress": 80},
    ]
    monkeypatch.setattr(dims, "_load", lambda name: fake if name == "goals" else [])
    r = dims.dimension_records()
    assert r["goals"]["active"] == 2
    assert r["goals"]["avg"] == 60
    assert r["goals"]["items"][0]["name"] == "Read 12 books"


def test_stats_read_goals_through_shared_store(monkeypatch):
    fake = [{"name": "Read 12 books", "progress": 40}]
    monkeypatch.setattr(LS, "_goals", lambda: fake)
    monkeypatch.setattr(LS, "_habits", lambda: [])
    monkeypatch.setattr(LS, "load_nutrition", lambda: [])
    monkeypatch.setattr(LS, "load_fitness", lambda: [])
    monkeypatch.setattr(LS, "load_focus", lambda: [])
    monkeypatch.setattr(LS, "load_mental", lambda: [])
    monkeypatch.setattr(LS, "load_sleep", lambda: [])
    monkeypatch.setattr(LS, "get_recent_memory", lambda days=7: [])
    monkeypatch.setattr(LS, "life", type("L", (), {
        "get_hydration": staticmethod(lambda: {"today": 0, "goal": 8}),
        "get_sleep": staticmethod(lambda: {"today": None, "avg_7d": 0}),
    }))
    s = LS.dimension_stats()
    assert s["goals"]["today"] == 40
    assert s["goals"]["week"]["active"] == 1
