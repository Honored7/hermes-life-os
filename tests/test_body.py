from __future__ import annotations
from datetime import date, timedelta
from wellness import body_report as BR


def test_hydration_report(monkeypatch):
    import storage
    from wellness import life
    monkeypatch.setattr(life, "get_hydration", lambda: {"today": 3, "goal": 8})
    monkeypatch.setattr(storage, "get_recent_memory", lambda days=7: [])
    r = BR.hydration_report()
    assert r["today"] == 3 and r["goal"] == 8
    assert len(r["week"]) == 7 and r["read"]


def test_set_hydration(monkeypatch):
    import storage
    monkeypatch.setattr(storage, "load_hydration", lambda: {"date": date.today().isoformat(), "today": 2, "goal": 8})
    monkeypatch.setattr(storage, "save_hydration", lambda h: None)
    monkeypatch.setattr(storage, "write_memory", lambda e: None)
    assert BR.set_hydration(5)["today"] == 5


def test_nutrition_report_and_delete(monkeypatch):
    import storage
    t = date.today().isoformat()
    meals = [{"date": t, "food": "oats", "calories": 300, "protein": 10, "carbs": 50, "fat": 5}]
    monkeypatch.setattr(storage, "load_nutrition", lambda: meals)
    r = BR.nutrition_report()
    assert r["today"]["meals"] == 1 and r["today"]["cal"] == 300
    assert BR.delete_meal(0)["logged"] is True
