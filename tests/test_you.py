from __future__ import annotations
import json
from wellness import you as Y


def _patch_all(monkeypatch, feel=9, wins=2, nights=8, pages=1, dreams=1, steady=3, doors=None):
    mem = ([{"type": "mood"}] * feel) + ([{"type": "preparation"}] * steady)
    monkeypatch.setattr(Y, "get_recent_memory", lambda days=3650: mem)
    monkeypatch.setattr(Y, "get_wins", lambda limit=1000: [object()] * wins)
    monkeypatch.setattr(Y, "load_sleep", lambda: [object()] * nights)
    monkeypatch.setattr(Y.journal, "list_entries", lambda: (
        [{"is_dream": False}] * pages) + ([{"is_dream": True}] * dreams))
    monkeypatch.setattr(Y, "load_tokens", lambda: {"google": {"a": 1}} if doors is None else {})


class TestMoments:
    def test_counts_and_earned(self, monkeypatch):
        _patch_all(monkeypatch)
        m = Y.moments()
        assert m["counts"]["feel"] == 9
        ids = {x["id"] for x in m["moments"]}
        assert {"feel", "wins", "steady", "nights", "pages", "dreams", "door"} <= ids
        assert m["next"] is None

    def test_empty_room_offers_first_invitation(self, monkeypatch):
        _patch_all(monkeypatch, feel=0, wins=0, nights=0, pages=0, dreams=0, steady=0, doors={})
        m = Y.moments()
        assert m["moments"] == []
        assert "first check-in" in m["next"]

    def test_no_points_no_streaks(self, monkeypatch):
        _patch_all(monkeypatch)
        m = Y.moments()
        for x in m["moments"]:
            assert "points" not in x["text"].lower()
            assert "streak" not in x["text"].lower()


class TestExport:
    def test_shape(self, monkeypatch):
        _patch_all(monkeypatch)
        monkeypatch.setattr(Y.ingest, "_read", lambda n: [])
        e = Y.export_all()
        assert e["app"] == "Motif"
        assert {"memory", "sleep", "journal", "vitals", "counts"} <= set(e)


class TestWipe:
    def test_clears_owned_stores_and_memory_file(self, monkeypatch, tmp_path):
        called = {}
        monkeypatch.setattr(Y, "save_sleep", lambda _: called.setdefault("sleep", True))
        monkeypatch.setattr(Y.journal, "clear_entries", lambda: called.setdefault("journal", True))
        monkeypatch.setattr(Y.ingest, "clear_vitals", lambda: called.setdefault("vitals", True))
        mem = tmp_path / "memory.jsonl"
        mem.write_text(json.dumps([{"type": "mood", "state": "sad"}]), encoding="utf-8")
        tokens = tmp_path / "integrations"; tokens.mkdir()
        (tokens / "calendar_tokens.json").write_text('{"google": {"a": 1}}', encoding="utf-8")
        monkeypatch.setattr(Y, "HERMES_DIR", tmp_path)
        r = Y.wipe_all()
        assert called.get("sleep") and called.get("journal") and called.get("vitals")
        assert "memory:memory.jsonl" in r["cleared"]
        assert json.loads(mem.read_text()) == []
        # subdir (tokens) untouched
        assert json.loads((tokens / "calendar_tokens.json").read_text()) == {"google": {"a": 1}}
