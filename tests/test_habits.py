from __future__ import annotations
from wellness import life_stats as LS


def test_old_habit_flame_survives_migration(monkeypatch):
    import storage
    habits = [{"name": "Old habit", "streak": 5, "best_streak": 6,
               "total_done": 9, "last_done": None, "created": "2026-01-01"}]
    monkeypatch.setattr(storage, "load_habits", lambda: habits)
    monkeypatch.setattr(storage, "save_habits", lambda h: None)
    LS.update_habit("Old habit", True)
    h = habits[0]
    assert h["streak"] >= 5, "flame must survive migration"
    assert h["total_done"] >= 9, "total_done must never decrease"
    assert len(h["history"]) >= 5


def test_no_duplicate_day(monkeypatch):
    import storage
    habits = [{"name": "Dup", "streak": 0, "best_streak": 0, "total_done": 0, "history": []}]
    monkeypatch.setattr(storage, "load_habits", lambda: habits)
    monkeypatch.setattr(storage, "save_habits", lambda h: None)
    LS.update_habit("Dup", True)
    LS.update_habit("Dup", True)
    assert len(habits[0]["history"]) == 1


def test_habit_management(monkeypatch):
    import storage
    from datetime import date
    today = date.today().isoformat()
    habits = [{"name": "Walk", "streak": 2, "best_streak": 3, "total_done": 5, "history": [today]}]
    goals = [{"name": "G", "source": "habit:Walk"}]
    saved = {"h": None, "g": None}
    monkeypatch.setattr(storage, "load_habits", lambda: habits)
    monkeypatch.setattr(storage, "save_habits", lambda h: saved.update(h=h))
    monkeypatch.setattr(storage, "load_goals", lambda: goals)
    monkeypatch.setattr(storage, "save_goals", lambda g: saved.update(g=g))

    assert LS.rename_habit("Walk", "Daily walk")["logged"] is True
    assert saved["h"][0]["name"] == "Daily walk"
    assert saved["g"][0]["source"] == "habit:Daily walk"

    assert LS.unmark_habit_today("Daily walk")["logged"] is True
    assert today not in saved["h"][0]["history"]

    assert LS.delete_habit("Daily walk")["logged"] is True
    assert saved["h"] == []
    assert saved["g"][0]["source"] is None
