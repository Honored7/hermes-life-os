"""Write-path tests: one gate, every dimension, validation before persist.

Each test proves the round trip writes -> reads: the write facade
persists through upstream tools, and the experience layer (built in the
previous migration) sees it. Storage is an isolated tmp HOME throughout.
"""
import importlib
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
DEMO = ROOT / "demo"


@pytest.fixture()
def iso_store(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    for mod in ("storage", "patterns", "analytics", "plugins", "tools"):
        sys.modules.pop(mod, None)
    sys.path.insert(0, str(DEMO))
    import storage as s

    importlib.reload(s)
    return s


def _today() -> str:
    return date.today().isoformat()


class TestWaterSleepMeal:
    def test_water_accumulates(self, iso_store):
        from superapp.surfaces import writes

        assert writes.log_water(2)["ok"] is True
        assert writes.log_water(3)["ok"] is True
        sys.path.insert(0, str(DEMO))
        assert iso_store.load_hydration()["today"] == 5
        mem = [e for e in iso_store.get_recent_memory(days=1)
               if e.get("type") == "hydration"]
        assert len(mem) == 2

    def test_sleep_visible_to_experience(self, iso_store):
        from superapp.experience import dimension_stats
        from superapp.surfaces import writes

        writes.log_sleep(7.5, quality=7)
        assert iso_store.load_sleep()[-1]["hours"] == 7.5
        assert dimension_stats()["sleep"]["week"]["avg_hours"] == 7.5

    def test_meal_totals(self, iso_store):
        from superapp.surfaces import writes

        writes.log_meal("oats", calories=350, meal_time="breakfast")
        writes.log_meal("soup", calories=400, meal_time="lunch")
        assert len(iso_store.load_nutrition()) == 2


class TestMoveFocusMind:
    def test_workout_week_count(self, iso_store):
        from superapp.surfaces import writes

        r = writes.log_workout("walk", duration_min=20)
        assert "1 workout(s)" in r["message"]
        assert iso_store.load_fitness()[-1]["type"] == "walk"

    def test_focus_deep_work(self, iso_store):
        from superapp.surfaces import writes

        r = writes.log_focus("thesis", duration_min=25, quality=8)
        assert "25 min" in r["message"]

    def test_stress_meditation_gratitude(self, iso_store):
        from superapp.surfaces import writes

        writes.log_stress(7, trigger="deadline")
        writes.log_meditation(10)
        writes.log_gratitude(["tea", "sun"])
        mental = iso_store.load_mental()
        types = [m.get("type") for m in mental]
        assert "meditation" in types and "gratitude" in types
        assert mental[0]["score"] == 7


class TestMoodDreamNote:
    def test_mood_feeds_mirror(self, iso_store):
        from superapp.experience import mood_weather
        from superapp.surfaces import writes

        writes.log_mood("anxious", severity=6, note="deadline")
        w = mood_weather()
        assert w["total"] == 1 and w["predominant"] == "anxious"

    def test_dream_recap(self, iso_store):
        from superapp.surfaces import writes

        r = writes.log_dream("flying over water", symbols=["water"],
                             tone="positive")
        assert "Tone: positive" in r["message"]

    def test_note_and_habit_goal(self, iso_store):
        from superapp.experience import alive
        from superapp.surfaces import writes

        writes.log_note("call mom")
        writes.update_habit("Walk", completed=True)
        writes.update_goal("Ship", progress=30, note="draft done")
        assert iso_store.load_habits()[0]["streak"] == 1
        assert iso_store.load_goals()[0]["progress"] == 30
        assert alive()["habits"] == ["Walk"]  # writes -> experience


class TestReliefOutcome:
    def test_outcome_personalizes_engine(self, iso_store):
        from superapp.relief import recommend
        from superapp.relief.ledger import StoreLedger
        from superapp.surfaces import writes

        from superapp.core import get_store

        writes.log_relief_outcome("Cold Water on Wrists", "angry",
                                  severity_before=8, severity_after=4,
                                  effectiveness=5)
        ledger = StoreLedger(get_store())
        assert ledger.effectiveness_for("Cold Water on Wrists") == 5
        res = recommend("angry", severity=8, ledger=ledger)
        assert res.recommendations


class TestDispatcher:
    def test_write_routes_every_kind(self, iso_store):
        from superapp.surfaces.writes import UnknownKindError, write

        assert write("water", {"glasses": 1})["kind"] == "water"
        assert write("sleep", {"hours": 6})["kind"] == "sleep"
        assert write("nutrition", {"food": "x"})["kind"] == "nutrition"
        assert write("workout", {"workout_type": "run",
                                 "duration_min": 10})["kind"] == "fitness"
        assert write("focus", {"task": "t"})["kind"] == "focus"
        assert write("stress", {"score": 5})["kind"] == "stress"
        assert write("meditation", {})["kind"] == "meditation"
        assert write("gratitude", {"items": ["a"]})["kind"] == "gratitude"
        assert write("mood", {"state": "good"})["kind"] == "mood"
        assert write("dream", {"content": "flying"})["kind"] == "dream"
        assert write("habit", {"name": "h"})["kind"] == "habit"
        assert write("goal", {"name": "g"})["kind"] == "goal"
        assert write("note", {"content": "n"})["kind"] == "note"
        with pytest.raises(UnknownKindError):
            write("teleport", {})

    def test_corrections(self, iso_store):
        from superapp.surfaces import writes
        from superapp.surfaces.writes import WriteValidationError

        writes.log_note("originaal typo")
        mem = iso_store.get_recent_memory(days=1)
        entry_id = mem[-1]["id"]
        r = writes.correct_entry(entry_id, {"content": "original fixed"})
        assert r["ok"] is True
        assert writes.delete_entry(entry_id)["ok"] is True
        with pytest.raises(WriteValidationError):
            writes.correct_entry("nope-nope", {"content": "x"})


class TestValidation:
    def test_rejects_garbage_before_persist(self, iso_store):
        from superapp.surfaces import writes
        from superapp.surfaces.writes import UnknownKindError  # noqa: F401
        from superapp.surfaces.writes import WriteValidationError

        before = iso_store.memory_count()
        bad_calls = [
            lambda: writes.log_water(-1),
            lambda: writes.log_water(0),
            lambda: writes.log_sleep(99),
            lambda: writes.log_stress(11),
            lambda: writes.log_meal("", calories=100),
            lambda: writes.log_meal("x", meal_time="brunch"),
            lambda: writes.log_workout("", duration_min=10),
            lambda: writes.log_focus("", duration_min=10),
            lambda: writes.log_gratitude([]),
            lambda: writes.log_mood("", severity=5),
            lambda: writes.log_dream(""),
            lambda: writes.update_habit(""),
            lambda: writes.update_goal(""),
            lambda: writes.write("relief", {"name": "x"}),
        ]
        for call in bad_calls:
            with pytest.raises((WriteValidationError, TypeError)):
                call()
        assert iso_store.memory_count() == before  # nothing persisted
