"""Upstream contract tests — Motif's early-warning radar.

Pin ONLY what the super-app seams rely on, never upstream internals:
dispatch tool names + params, storage loader names + record shapes,
pattern/correlation outputs, scheduler modes, notification channels.

If upstream renames, reshapes, or removes any of it, THIS suite goes red
on THEIR change — before any user sees it. Run it (plus everything else)
after every `git fetch upstream` before moving UPSTREAM_SNAPSHOT.

Conventions match the rest of the suite: demo/ on sys.path, storage
reloaded under a tmp HOME so no test touches the real ~/.hermes.
"""
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
DEMO = ROOT / "demo"

DEMO_MODULES = ("storage", "patterns", "analytics", "plugins", "tools")


@pytest.fixture()
def demo(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    for mod in DEMO_MODULES:
        sys.modules.pop(mod, None)
    sys.path.insert(0, str(DEMO))
    import storage
    import tools

    importlib.reload(storage)
    importlib.reload(tools)
    return storage, tools


WRITE_TOOLS = {
    # tool name -> minimal valid payload (must persist without raising)
    "log_hydration": {"glasses": 1},
    "log_sleep": {"hours": 7.0, "quality": 6},
    "log_meal": {"food": "oats", "calories": 300,
                 "meal_time": "breakfast"},
    "log_workout": {"workout_type": "walk", "duration_min": 20},
    "log_focus_session": {"task": "thesis", "duration_min": 25},
    "log_stress": {"score": 5, "trigger": "test"},
    "log_meditation": {"duration_min": 10},
    "log_gratitude": {"items": ["tea"]},
    "remember": {"type": "note", "content": "contract probe"},
    "log_dream": {"content": "flying"},
    "log_expense": {"amount": 5, "category": "food"},
    "log_social_interaction": {"with_who": "sam", "quality": 7},
    "log_substance": {"substance": "coffee", "amount": 1,
                      "unit": "cup"},
    "log_reading": {"title": "Meditations", "minutes": 20},
    "log_medication": {"name": "d3", "taken": True},
    "update_habit": {"habit_name": "Probe", "completed": True},
    "update_goal": {"goal_name": "Probe", "progress": 10},
    "correct_entry": {"entry_id": "nope", "updates": {"content": "x"}},
    "delete_entry": {"entry_id": "nope"},
}


class TestDispatchContract:
    @pytest.mark.parametrize("tool,payload",
                             list(WRITE_TOOLS.items()))
    def test_write_tool_accepts(self, demo, tool, payload):
        _, tools = demo
        result = tools.dispatch_tool(tool, dict(payload))
        assert "Unknown tool" not in result, tool

    def test_unknown_tool_reported(self, demo):
        _, tools = demo
        assert "Unknown tool" in tools.dispatch_tool("teleport", {})

    def test_tool_registry_lists_ours(self, demo):
        _, tools = demo
        names = {t["function"]["name"] for t in tools.TOOLS}
        for tool in WRITE_TOOLS:
            assert tool in names, tool


class TestStorageContract:
    LOADERS = ("load_profile", "load_habits", "load_goals",
               "load_nutrition", "load_sleep", "load_hydration",
               "load_fitness", "load_focus", "load_mental",
               "load_spending", "load_social", "load_substance",
               "load_reading", "load_medication")

    def test_loaders_exist_and_default(self, demo):
        storage, _ = demo
        for name in self.LOADERS:
            assert callable(getattr(storage, name, None)), name
        assert storage.load_profile() == {"name": "friend",
                                          "onboarded": False}
        assert storage.load_habits() == []

    def test_sleep_record_shape(self, demo):
        storage, tools = demo
        tools.dispatch_tool("log_sleep", {"hours": 7.5, "quality": 7})
        entry = storage.load_sleep()[-1]
        assert entry["hours"] == 7.5
        assert entry["quality"] == 7
        assert entry["date"]

    def test_memory_journal_roundtrip(self, demo):
        storage, _ = demo
        storage.write_memory({"type": "note", "content": "probe-xyz"})
        assert storage.memory_count() >= 1
        hits = storage.search_memory("probe-xyz", limit=5)
        assert hits and hits[-1]["content"] == "probe-xyz"
        assert storage.get_recent_memory(days=7)


class TestIntelligenceContract:
    def test_detect_patterns_keys(self, demo):
        sys.path.insert(0, str(DEMO))
        import patterns as upstream_patterns

        result = upstream_patterns.detect_patterns()
        assert isinstance(result, dict)
        assert "insights" in result and "correlation_details" in result

    def test_pearson_contract(self, demo):
        sys.path.insert(0, str(DEMO))
        import analytics as upstream_analytics

        assert upstream_analytics.pearson_correlation(
            [1, 2, 3, 4], [2, 4, 6, 8]) == pytest.approx(1.0)
        assert upstream_analytics.pearson_correlation(
            [5, 5, 5, 5], [1, 2, 3, 4]) is None


class TestSchedulerContract:
    def test_default_modes_stable(self):
        sys.path.insert(0, str(DEMO))
        import scheduler as upstream_scheduler

        modes = {e.mode for e in upstream_scheduler.default_schedule()}
        assert {"morning", "checkin", "evening", "weekly",
                "nudge_check", "backup"} <= modes

    def test_runner_notifier_injection(self):
        sys.path.insert(0, str(DEMO))
        import scheduler as upstream_scheduler
        from datetime import datetime

        seen = []
        entries = [upstream_scheduler.ScheduleEntry("07:00", "morning")]
        upstream_scheduler.run_scheduler(
            entries, runner=lambda m: "hello",
            notifier=lambda t, c: seen.append((t, c)),
            max_iterations=1, clock=lambda: datetime(2026, 9, 14, 7, 0),
            sleeper=lambda s: None)
        assert seen and seen[0][1] == "hello"

    def test_console_notify_ok(self):
        sys.path.insert(0, str(DEMO))
        from notifications import send_notification

        assert send_notification("t", "probe",
                                 channel="console").ok is True
