from __future__ import annotations
from wellness import life_stats as LS


def _empty(monkeypatch):
    for fn in ["load_nutrition", "load_sleep", "load_fitness",
               "load_focus", "load_mental", "load_habits", "load_goals"]:
        monkeypatch.setattr(LS, fn, lambda: [])
    monkeypatch.setattr(LS, "get_recent_memory", lambda days=7: [])
    monkeypatch.setattr(LS.life, "get_hydration", lambda: {"today": 0, "goal": 8})
    monkeypatch.setattr(LS.life, "get_sleep", lambda: {"today": None, "avg_7d": 0})


def test_stats_shape_when_empty(monkeypatch):
    _empty(monkeypatch)
    s = LS.dimension_stats()
    assert set(s) == {"hydration", "sleep", "nutrition", "fitness", "focus", "mental", "habits", "goals"}
    assert all(len(s[d]["series"]) == 7 for d in ("hydration", "sleep", "nutrition", "fitness", "focus", "mental"))
    assert s["hydration"]["unit"] == "glasses"
    assert s["nutrition"]["unit"] == "kcal"
    assert s["sleep"]["unit"] == "h"


def test_log_functions_write(monkeypatch, tmp_path):
    store = []
    monkeypatch.setattr(LS, "save_nutrition", lambda v: store.extend(v) or None)
    monkeypatch.setattr(LS, "load_nutrition", lambda: [])
    monkeypatch.setattr(LS, "write_memory", lambda e: None)
    LS.log_nutrition("oats", 300, "breakfast")
    assert store and store[0]["food"] == "oats"
