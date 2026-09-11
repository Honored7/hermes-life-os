"""Rhythm tests: renderers speak specifically, the loop fires once.

The scheduler itself stays upstream-owned; these tests prove our side
of the seam (runner content + notifier delivery + no double-fire),
always under an isolated tmp HOME with an injectable clock.
"""
import importlib
import sys
from datetime import datetime
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


def _seed_day(s):
    from superapp.surfaces import writes

    writes.log_sleep(7.2, quality=7)
    writes.update_habit("Walk", completed=True)
    writes.log_mood("good", severity=3, note="light")


class TestRenderers:
    def test_morning_names_real_things(self, iso_store):
        _seed_day(iso_store)
        from superapp.surfaces.rhythm import render_morning

        text = render_morning()
        assert "7.2h" in text  # specificity, not a generic greeting
        assert "Walk" in text

    def test_morning_empty_invites(self, iso_store):
        from superapp.surfaces.rhythm import render_morning

        assert "fresh page" in render_morning()

    def test_checkin_suggests(self, iso_store):
        from superapp.surfaces.rhythm import render_checkin

        assert "Midday check-in." in render_checkin()

    def test_evening_closes(self, iso_store):
        _seed_day(iso_store)
        from superapp.surfaces.rhythm import render_evening

        text = render_evening()
        assert "closing" in text and "win" in text

    def test_weekly_reviews(self, iso_store):
        _seed_day(iso_store)
        from superapp.surfaces.rhythm import render_weekly

        assert "shape of you" in render_weekly()

    def test_weekly_empty_gathers(self, iso_store):
        from superapp.surfaces.rhythm import render_weekly

        assert "gathering" in render_weekly()


class TestRunner:
    def test_modes_render(self, iso_store):
        _seed_day(iso_store)
        from superapp.surfaces.rhythm import make_runner

        runner = make_runner()
        for mode in ("morning", "checkin", "evening", "weekly"):
            assert runner(mode).strip(), mode

    def test_unknown_mode_silent(self, iso_store):
        from superapp.surfaces.rhythm import make_runner

        assert make_runner()("bogus_mode_xyz") == ""

    def test_runner_never_raises(self, iso_store, monkeypatch):
        from superapp.surfaces import rhythm as rhythm_mod

        def boom():
            raise RuntimeError("renderer exploded")

        monkeypatch.setitem(rhythm_mod._RENDERERS, "morning", boom)
        assert rhythm_mod.make_runner()("morning") == ""


class TestLoopAndDelivery:
    def test_morning_fires_once_at_0700(self, iso_store):
        _seed_day(iso_store)
        from superapp.surfaces.rhythm import run_rhythm

        sent = []

        def fake_clock():
            return datetime(2026, 9, 14, 7, 0)  # a Monday

        import superapp.surfaces.rhythm as rhythm_mod

        real_notifier = rhythm_mod.make_notifier

        def capture_notifier(channel=None):
            base = real_notifier(channel)

            def capture(title, content):
                sent.append((title, content))
                return base(title, content)

            return capture

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(rhythm_mod, "make_notifier", capture_notifier)
        try:
            run_rhythm(max_iterations=2, clock=fake_clock,
                       sleeper=lambda s: None)
        finally:
            monkeypatch.undo()
        mornings = [t for t, _ in sent if "Morning" in t]
        assert len(mornings) == 1  # due once, never double-fired
        assert "7.2h" in sent[0][1]

    def test_notifier_console_ok(self, iso_store, capsys):
        from superapp.surfaces.rhythm import make_notifier

        result = make_notifier("console")("Test", "hello")
        assert result.ok is True
        assert "hello" in capsys.readouterr().out
