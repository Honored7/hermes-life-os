from __future__ import annotations
from wellness import journal as J


def test_tag_dream_picks_themes():
    tags = J.tag_dream("I was flying over a dark sea, then woke cold")
    assert "movement" in tags and "water" in tags and "shadow" in tags


def test_tag_dream_empty_for_plain_text():
    assert J.tag_dream("had a sandwich and a nap") == []


def test_add_list_delete_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(J, "ENTRIES_FILE", tmp_path / "e.json")
    monkeypatch.setattr(J, "JOURNAL_DIR", tmp_path)
    e = J.add_entry("<p>flying over a dark sea</p>", "flying over a dark sea", is_dream=True)
    assert e["is_dream"] is True and "movement" in e["tags"]
    assert len(J.list_entries()) == 1
    assert J.delete_entry(e["id"]) is True
    assert J.list_entries() == []
    assert J.delete_entry("nope") is False
