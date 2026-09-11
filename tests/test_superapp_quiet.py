"""Quiet dimensions: blend, never replace. The 9 stay; the 5 join calmly.

Proves the registry promise: each new dimension is a writes kind, a
reads builder, and API rows — no new code paths, no punished users.
"""
import importlib
import sys
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


class TestWritesFive:
    def test_spending_roundtrip(self, iso_store):
        from superapp.surfaces import writes

        r = writes.log_spending(12.5, category="food")
        assert r["ok"] and "12.5" in r["message"]
        assert writes.write("spending", {"amount": 3})["kind"] == "spending"
        with pytest.raises(Exception):
            writes.log_spending(-1)
        with pytest.raises(Exception):
            writes.log_spending("not-money")

    def test_social_roundtrip(self, iso_store):
        from superapp.surfaces import writes

        r = writes.log_social("Sam", quality=8, duration_min=60)
        assert r["ok"]
        assert writes.write("social", {"with_who": "Jo"})["kind"] == "social"
        with pytest.raises(Exception):
            writes.log_social("", quality=5)
        with pytest.raises(Exception):
            writes.log_social("Sam", quality=11)

    def test_substance_roundtrip(self, iso_store):
        from superapp.surfaces import writes

        r = writes.log_substance("coffee", amount=2, unit="cups")
        assert r["ok"]
        assert writes.write("substance", {"substance": "tea"})["kind"] \
            == "substance"
        with pytest.raises(Exception):
            writes.log_substance("", amount=1)

    def test_reading_roundtrip(self, iso_store):
        from superapp.surfaces import writes

        r = writes.log_reading("Meditations", minutes=20, pages=15)
        assert r["ok"]
        assert writes.write("reading", {"title": "x"})["kind"] == "reading"
        with pytest.raises(Exception):
            writes.log_reading("", minutes=5)

    def test_medication_roundtrip(self, iso_store):
        from superapp.surfaces import writes

        r = writes.log_medication("d3", taken=True)
        assert r["ok"]
        writes.log_medication("d3", taken=False)
        assert writes.write("medication", {"name": "d3"})["kind"] \
            == "medication"
        with pytest.raises(Exception):
            writes.log_medication("")


class TestReadsBlend:
    def test_nine_intact_five_join(self, iso_store):
        from superapp.experience import dimension_stats

        d = dimension_stats()
        nine = {"hydration", "sleep", "nutrition", "fitness", "focus",
                "mental", "habits", "goals"}
        five = {"spending", "social", "substance", "reading",
                "medication"}
        assert nine <= set(d)  # nothing disappeared
        assert five <= set(d)  # the blend
        for name in five:
            card = d[name]
            assert set(card) >= {"unit", "target", "lower_better",
                                 "today", "series", "week", "list"}

    def test_quiet_copy_never_punishes(self, iso_store):
        from superapp.experience import dimension_stats

        d = dimension_stats()
        text = " ".join(str(v) for name in
                        ("spending", "substance", "medication")
                        for v in (d[name]["week"],)).lower()
        for word in ("shame", "failed", "missed", "broken", "bad"):
            assert word not in text

    def test_spending_math(self, iso_store):
        from superapp.experience import dimension_stats
        from superapp.surfaces import writes

        writes.log_spending(10, category="food")
        writes.log_spending(20, category="food")
        writes.log_spending(5, category="bus")
        d = dimension_stats()["spending"]
        assert d["today"] == 35
        assert d["week"]["top_category"] == "food"

    def test_medication_adherence(self, iso_store):
        from superapp.experience import dimension_stats
        from superapp.surfaces import writes

        writes.log_medication("d3", taken=True)
        writes.log_medication("d3", taken=False)
        week = dimension_stats()["medication"]["week"]
        assert week == {"taken": 1, "logged": 2, "adherence_pct": 50}

    def test_registry_is_the_only_way(self):
        from superapp.experience.quiet import QUIET_DIMS

        assert set(QUIET_DIMS) == {"spending", "social", "substance",
                                   "reading", "medication"}
        for name, build in QUIET_DIMS.items():
            card = build()
            assert card["week"] is not None, name


class TestApiFive:
    def test_dim_endpoints(self):
        from fastapi.testclient import TestClient

        from superapp.surfaces.api import app

        c = TestClient(app)
        for dim in ("spending", "social", "substance", "reading",
                    "medication"):
            r = c.get(f"/api/v1/life/{dim}")
            assert r.status_code == 200, dim
            assert "week" in r.json()
