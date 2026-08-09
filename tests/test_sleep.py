from __future__ import annotations
from datetime import date, timedelta
from wellness import sleep_report as SR


def _nights():
    d1 = (date.today() - timedelta(days=1)).isoformat()
    d2 = (date.today() - timedelta(days=2)).isoformat()
    return [{"date": d1, "hours": 7.5, "quality": 7},
            {"date": d2, "hours": 5, "quality": 4}]


def test_sleep_report_shape(monkeypatch):
    import storage
    monkeypatch.setattr(storage, "load_sleep", lambda: _nights())
    r = SR.sleep_report()
    assert r["nights_logged"] == 2
    assert r["target"] == 7.5
    assert len(r["week"]) == 7
    assert r["avg_hours"] > 0
    assert r["read"]


def test_delete_sleep(monkeypatch):
    import storage
    monkeypatch.setattr(storage, "load_sleep", lambda: _nights())
    monkeypatch.setattr(storage, "save_sleep", lambda x: None)
    d = (date.today() - timedelta(days=1)).isoformat()
    assert SR.delete_sleep(d)["logged"] is True
