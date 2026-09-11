"""Experience migration tests: briefing, mirror/climate, keepsake, journal.

Every room is proven twice: empty (invitation, never crash) and seeded
(specific, data-backed — the Motif specificity rule). Storage is always
an isolated tmp HOME; the experience shim reads the reloaded module live.
"""
import importlib
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

DEMO = ROOT / "demo"


@pytest.fixture()
def iso_store(tmp_path, monkeypatch):
    """Reload upstream storage under a tmp HOME; return the module."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    for mod in ("storage", "patterns", "analytics", "plugins", "tools"):
        sys.modules.pop(mod, None)
    sys.path.insert(0, str(DEMO))
    import storage as s

    importlib.reload(s)
    return s


def _day_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def _seed_mood_sleep(s, days: int = 6, correlated: bool = True):
    """Seed paired sleep + mood days. Correlated: long sleep, bright mood."""
    sleeps = []
    for i in range(days):
        d = _day_ago(days - 1 - i)
        hours = 5.0 + i * 0.6 if correlated else 8.0
        sleeps.append({"date": d, "hours": round(hours, 1), "quality": 6})
        s.write_memory({
            "type": "mood", "state": "good" if hours > 6.5 else "sad",
            "mood": round(3 + i, 1), "date": d,
        })
    s.save_sleep(sleeps)


class TestBriefing:
    def test_empty_invitation(self, iso_store):
        from superapp.experience import briefing

        b = briefing()
        assert b["true_line"].endswith("what will you tend first?")
        assert b["suggestion"]["kind"] == "water"  # thirst first
        assert set(b) >= {"part", "greeting", "true_line", "suggestion"}

    def test_specific_true_line(self, iso_store):
        iso_store.save_sleep(
            [{"date": _day_ago(0), "hours": 7.2, "quality": 7}])
        iso_store.save_habits(
            [{"name": "Walk", "streak": 3, "best_streak": 5,
              "log": {}}])
        from superapp.experience import alive, briefing

        b = briefing()
        assert "7.2h" in b["true_line"]  # specificity, not "Good morning"
        assert "1 habit" in b["true_line"]
        a = alive()
        assert a["habits"] == ["Walk"]
        assert a["move_min"] == 0


class TestMirror:
    def test_empty_gathering(self, iso_store):
        from superapp.experience import mirror

        m = mirror()
        assert m["threads"] == []
        assert "gathering" in m["reflection"]

    def test_sleep_mood_thread(self, iso_store):
        _seed_mood_sleep(iso_store)
        from superapp.experience import mirror

        m = mirror()
        assert m["threads"], "6 correlated days must surface a thread"
        top = max(m["threads"], key=lambda t: t["strength"])
        assert top["a"] == "sleep" and top["b"] == "mood"
        assert top["r"] > 0.3
        assert "question" in m and m["question"] is not None

    def test_dateless_entries_use_timestamp(self, iso_store):
        # Upstream writers stamp timestamp only (no 'date' field).
        # The rooms must still see those entries via timestamp fallback.
        from superapp.experience import climate, mirror

        for i in range(6):
            iso_store.save_sleep(
                iso_store.load_sleep() + [{"date": _day_ago(i), "hours": 7.0,
                                           "quality": 6}])
        iso_store.write_memory({"type": "mood", "state": "good",
                                "mood": 7.0})  # no 'date' key
        m = mirror()
        today = _day_ago(0)
        tap = [t for t in m["tapestry"] if t["date"] == today][0]
        assert tap["mood"] == pytest.approx(0.7)
        c = climate()
        assert c["span"] >= 6  # sleep-file dates carry the span

    def test_shared_pearson(self):
        from superapp.intelligence import pearson

        assert pearson([1, 2, 3, 4], [2, 4, 6, 8]) == pytest.approx(1.0)
        assert pearson([1, 2, 3], [1, 2, 3]) is None  # <4 points: silence
        assert pearson([5, 5, 5, 5], [1, 2, 3, 4]) is None  # no variance


class TestClimate:
    def test_empty_invitation(self, iso_store):
        from superapp.experience import climate

        c = climate()
        assert c["span"] == 0 and c["cards"] == []
        assert len(c["empty"]) == 4 and c["signals"] == {
            "correlations": [], "patterns": []}

    def test_seeded_cards_and_signals(self, iso_store):
        for i in range(20):
            d = _day_ago(19 - i)
            mood = 4.0 if i < 14 else 8.0  # heavy then, bright now
            iso_store.write_memory(
                {"type": "mood", "state": "sad" if mood < 6 else "good",
                 "mood": mood, "date": d})
            iso_store.write_memory(
                {"type": "stress", "score": 7, "date": d})
        iso_store.save_sleep(
            [{"date": _day_ago(i), "hours": 5.5, "quality": 4}
             for i in range(10)])
        from superapp.experience import climate

        c = climate()
        assert c["span"] > 0
        assert "shape of you" in c["headline"]
        kinds = {card["id"] for card in c["cards"]}
        assert "rest" in kinds  # short sleep + high stress surface
        assert set(c["signals"]) == {"correlations", "patterns"}

    def test_mood_weather_and_trend(self, iso_store):
        for i in range(5):
            iso_store.write_memory(
                {"type": "mood", "state": "good", "severity": 3,
                 "date": _day_ago(i)})
        from superapp.experience import mood_trend, mood_weather

        w = mood_weather()
        assert w["total"] == 5 and w["predominant"] == "good"
        t = mood_trend()
        assert t["series"] and t["direction"] in (
            "none", "holding", "warmer", "cooler")


class TestKeepsake:
    def test_empty_letter(self, iso_store):
        from superapp.experience import keepsake

        k = keepsake()
        assert k["letter"][0].startswith("I've been watching")
        assert k["recognitions"] == []
        assert k["moments"] == []

    def test_seeded_recognitions(self, iso_store):
        for i in range(6):
            iso_store.write_memory(
                {"type": "stress", "score": 7, "date": _day_ago(i)})
        for i in range(4):
            iso_store.write_memory(
                {"type": "gratitude", "items": ["tea"], "date": _day_ago(i)})
        iso_store.save_habits(
            [{"name": "Walk", "streak": 2, "best_streak": 9, "log": {}}])
        iso_store.save_goals(
            [{"name": "Ship", "progress": 100, "milestones": []}])
        from superapp.experience import keepsake

        k = keepsake()
        text = " ".join(k["recognitions"])
        assert "stress" in text and "good things" in text
        assert "9 days" in text and "completed 1 goal" in text

    def test_moments_counts(self, iso_store):
        iso_store.write_memory(
            {"type": "mood", "state": "good", "content": "light",
             "date": _day_ago(0)})
        from superapp.experience import moments

        m = moments()
        assert m["counts"]["feel"] == 1
        assert m["moments"] and m["next"] is not None


class TestJournalAndRhythm:
    def test_journal_roundtrip(self, iso_store):
        from superapp.experience import (
            add_entry,
            delete_entry,
            list_entries,
        )

        entry = add_entry("<p>held</p>", "held", False)
        assert entry["id"]
        assert len(list_entries()) == 1
        assert delete_entry(entry["id"]) is True
        assert list_entries() == []

    def test_sleep_rhythm(self, iso_store):
        iso_store.save_sleep(
            [{"date": _day_ago(i), "hours": 5.0, "quality": 3}
             for i in range(3)])
        from superapp.experience import rhythm_payload

        r = rhythm_payload()
        assert r["poor_streak"] == 3
        assert r["avg_hours"] == 5.0

    def test_dimension_stats_shape(self, iso_store):
        iso_store.save_sleep(
            [{"date": _day_ago(0), "hours": 7.0, "quality": 6}])
        from superapp.experience import dimension_stats

        d = dimension_stats()
        assert set(d) >= {"hydration", "sleep", "nutrition", "fitness",
                          "focus", "mental", "habits", "goals"}
        assert d["sleep"]["week"]["avg_hours"] == 7.0


class TestKeepersDoor:
    def test_export_then_wipe(self, iso_store):
        iso_store.write_memory({"type": "mood", "content": "blue"})
        iso_store.save_sleep([{"date": _day_ago(0), "hours": 6.0}])
        from superapp.experience import add_entry
        from superapp.surfaces.keepers import export_all, wipe_all

        add_entry("<p>x</p>", "x", False)
        exp = export_all()
        assert exp["app"] == "Motif"
        assert exp["counts"]["feel"] == 1  # the seeded mood entry
        assert exp["sleep"] != []

        wiped = wipe_all()
        assert "sleep" in wiped["cleared"]
        assert "journal" in wiped["cleared"]
        assert "vitals" in wiped["cleared"]
