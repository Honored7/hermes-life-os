"""Whispers: one specific line per context, never filler, never a chat."""
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


class TestWhispers:
    def test_empty_invites(self, iso_store):
        from superapp.experience import whisper

        for dim in ("sleep", "spending", "medication", "social",
                    "substance", "reading", "today"):
            line = whisper(dim)
            assert line["dimension"] == dim
            assert len(line["text"]) > 20

    def test_specific_not_generic(self, iso_store):
        from superapp.experience import whisper
        from superapp.surfaces import writes

        writes.log_sleep(5.5, quality=4)
        writes.log_spending(42, category="food")
        assert "5.5h" in whisper("sleep")["text"]
        assert "$42" in whisper("spending")["text"]

    def test_calm_copy(self, iso_store):
        import re

        from superapp.experience import whisper

        text = " ".join(whisper(d)["text"] for d in
                        ("spending", "substance", "medication")).lower()
        words = set(re.findall(r"[a-z]+", text))
        for word in ("shame", "failed", "broken", "bad"):
            assert word not in words

    def test_unknown_dimension_graceful(self, iso_store):
        from superapp.experience import whisper

        line = whisper("teleport")
        assert line["dimension"] == "teleport"
        assert len(line["text"]) > 10

    def test_http(self, iso_store):
        from fastapi.testclient import TestClient

        from superapp.surfaces.api import app

        c = TestClient(app)
        r = c.get("/api/v1/whisper", params={"dimension": "sleep"})
        assert r.status_code == 200 and "text" in r.json()
        assert "text" in c.get("/api/v1/whisper/today").json()
