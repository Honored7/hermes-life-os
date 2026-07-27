from __future__ import annotations
from wellness import dimensions as D


def _mem(rows):
    return [
        {"type": t, "date": d, **vals, "timestamp": d + "T08:00:00Z"}
        for (t, d, vals) in rows
    ]


class TestSeries:
    def test_generic_extractor_reads_value_key(self, monkeypatch):
        mem = _mem([
            ("hydration", "2026-07-20", {"glasses": 5}),
            ("hydration", "2026-07-21", {"glasses": 8}),
            ("hydration", "2026-07-21", {"glasses": 2}),  # same day -> averaged
        ])
        monkeypatch.setattr(D, "_memory", lambda: mem)
        s = D._series_for("hydration", mem)
        assert s["2026-07-20"] == 5.0
        assert s["2026-07-21"] == 5.0

    def test_ignores_other_types_and_bad_values(self, monkeypatch):
        mem = _mem([
            ("focus", "2026-07-20", {"quality": 7}),
            ("hydration", "2026-07-20", {"glasses": 9}),
            ("focus", "2026-07-21", {"quality": "oops"}),
        ])
        s = D._series_for("focus", mem)
        assert s == {"2026-07-20": 7.0}


class TestEdges:
    def test_no_edge_without_enough_paired_days(self):
        assert D._edges({"sleep": {"a": 5, "b": 8}, "focus": {"a": 3}}) == {}

    def test_low_sleep_low_focus_yields_a_focus_edge(self):
        sleep = {"d1": 5, "d2": 5, "d3": 5, "d4": 8, "d5": 8, "d6": 8}
        focus = {"d1": 3, "d2": 4, "d3": 3, "d4": 8, "d5": 9, "d6": 8}
        edges = D._edges({"sleep": sleep, "focus": focus})
        assert "focus" in edges and "sleep" in edges["focus"]

    def test_no_edge_when_no_relationship(self):
        sleep = {"d1": 5, "d2": 5, "d3": 5, "d4": 8, "d5": 8, "d6": 8}
        focus = {"d1": 7, "d2": 7, "d3": 7, "d4": 7, "d5": 7, "d6": 7}
        assert D._edges({"sleep": sleep, "focus": focus}) == {}


class TestStats:
    def test_shape_with_empty_stores(self, monkeypatch):
        monkeypatch.setattr(D, "_memory", lambda: [])
        monkeypatch.setattr(D, "sleep_summary", lambda: {"series": [], "last_hours": None,
                                                         "avg_hours": None, "poor_streak": 0, "count": 0})
        monkeypatch.setattr(D, "mood_weather", lambda days=7: {"predominant": None, "temperature": None, "total": 0})
        out = D.dimension_stats()
        assert set(out["dims"]) >= {"sleep", "mood", "hydration", "focus"}
        assert out["edges"] == {}
        assert out["sleep"]["count"] == 0
