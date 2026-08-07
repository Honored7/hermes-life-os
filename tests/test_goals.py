from __future__ import annotations
from datetime import date, timedelta
from wellness import goals as G


def test_manual_count_goal_pct():
    g = G.compute_goal({"name": "Read 5 books", "unit": "books", "target": 5, "count": 2})
    assert g["pct"] == 40
    assert g["count"] == 2


def test_legacy_progress_fallback():
    g = G.compute_goal({"name": "Old goal", "progress": 60})
    assert g["pct"] == 60


def test_dim_fitness_counts_this_week(monkeypatch):
    import storage
    ws = date.today() - timedelta(days=date.today().weekday())
    monkeypatch.setattr(storage, "load_fitness", lambda: [
        {"date": ws.isoformat(), "type": "gym"},
        {"date": (ws + timedelta(days=1)).isoformat(), "type": "run"},
        {"date": "2000-01-01", "type": "old"},
    ])
    g = G.compute_goal({"name": "Work out 3x", "unit": "workouts", "target": 3, "source": "dim:fitness"})
    assert g["count"] == 2
    assert g["pct"] == 67


def test_habit_fed_goal(monkeypatch):
    import storage
    monkeypatch.setattr(storage, "load_habits", lambda: [
        {"name": "Read nightly", "total_done": 3},
    ])
    g = G.compute_goal({"name": "Read 5 books", "unit": "books", "target": 5, "source": "habit:Read nightly"})
    assert g["count"] == 3
    assert g["pct"] == 60


def test_habit_hint_heuristic():
    assert "read" in G.habit_hint_for("Read 5 books", "books").lower()
    assert G.habit_hint_for("anything", "") != ""


def test_pace_behind_and_ahead():
    created = (date.today() - timedelta(days=30)).isoformat()
    dl = (date.today() + timedelta(days=30)).isoformat()
    behind = G.pace_note({"deadline": dl, "created": created, "unit": "books"}, 1, 12)
    assert behind and "behind" in behind
    ahead = G.pace_note({"deadline": dl, "created": created, "unit": "books"}, 11, 12)
    assert ahead and "ahead" in ahead


def test_increment_and_bump(monkeypatch, tmp_path):
    import storage
    goals = [{"name": "Read 5 books", "count": 1}]
    habits = [{"name": "Read nightly", "total_done": 0}]
    monkeypatch.setattr(storage, "load_goals", lambda: goals)
    monkeypatch.setattr(storage, "save_goals", lambda g: None)
    monkeypatch.setattr(storage, "load_habits", lambda: habits)
    monkeypatch.setattr(storage, "save_habits", lambda h: None)
    G.increment_goal("Read 5 books")
    assert goals[0]["count"] == 2
    # bump_habit_total is now a no-op; update_habit owns total_done.
    G.bump_habit_total("Read nightly")
    assert habits[0]["total_done"] == 0
    from wellness import life_stats as LS
    LS.update_habit("Read nightly", True)
    assert habits[0]["total_done"] == 1


def test_step_goal_next_rung():
    g = G.compute_goal({"name": "Write a book", "steps": [
        {"name": "outline", "done": True},
        {"name": "draft", "done": False},
        {"name": "edit", "done": False},
        {"name": "publish", "done": False},
    ]})
    assert g["pct"] == 25 and g["count"] == 1 and g["target"] == 4
    assert g["next_step"]["name"] == "draft" and g["next_step"]["index"] == 1


def test_add_and_toggle_step(monkeypatch):
    import storage
    goals = [{"name": "Book", "steps": [{"name": "outline", "done": False}]}]
    monkeypatch.setattr(storage, "load_goals", lambda: goals)
    monkeypatch.setattr(storage, "save_goals", lambda g: None)
    G.add_goal_step("Book", "draft")
    assert goals[0]["steps"][1]["name"] == "draft"
    G.set_goal_step("Book", 0, True)
    assert goals[0]["steps"][0]["done"] is True
