"""API skin tests: every room answers over HTTP (FastAPI TestClient).

Runs against an isolated tmp HOME via fixture. No network, no server.
"""
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
DEMO = ROOT / "demo"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    for mod in ("storage", "patterns", "analytics", "plugins", "tools"):
        sys.modules.pop(mod, None)
    sys.path.insert(0, str(DEMO))
    import storage as s

    importlib.reload(s)
    from fastapi.testclient import TestClient

    from superapp.surfaces.api import app

    return TestClient(app)


class TestRoomsOverHttp:
    def test_today(self, client):
        assert client.get("/api/v1/today/briefing").status_code == 200
        body = client.get("/api/v1/today/briefing").json()
        assert "true_line" in body
        assert "habits" in client.get("/api/v1/today/alive").json()

    def test_life_reads(self, client):
        for path in ("stats", "today", "dims", "dimensions", "sleep",
                     "hydration", "nutrition", "fitness", "focus", "mental"):
            r = client.get(f"/api/v1/life/{path}")
            assert r.status_code == 200, path

    def test_log_dim_roundtrip(self, client):
        r = client.post("/api/v1/life/log-dim",
                        json={"kind": "water", "glasses": 2})
        assert r.status_code == 200 and r.json()["ok"] is True
        assert client.post("/api/v1/life/log-dim",
                           json={"kind": "teleport"}).status_code == 400
        assert client.post("/api/v1/life/log-dim",
                           json={"kind": "sleep",
                                 "hours": 99}).status_code == 400

    def test_journal_crud(self, client):
        entry = client.post("/api/v1/life/journal",
                            json={"text": "held"}).json()["entry"]
        assert client.get("/api/v1/life/journal").json()["entries"]
        assert client.delete(
            f"/api/v1/life/journal/{entry['id']}").json()["deleted"] is True

    def test_insights(self, client):
        assert client.get("/api/v1/insights/climate").json()["span"] == 0
        for path in ("mirror", "mood-weather", "mood-trend", "rhythm"):
            assert client.get(f"/api/v1/insights/{path}").status_code == 200

    def test_you(self, client):
        assert "letter" in client.get("/api/v1/you/keepsake").json()
        assert "moments" in client.get("/api/v1/you/moments").json()
        assert client.get("/api/v1/you/export").json()["app"] == "Motif"

    def test_relief_library_and_wizard(self, client):
        assert len(client.get("/api/v1/interventions").json()) == 24
        assert client.get(
            "/api/v1/interventions/by-state/angry").json()
        r = client.post("/api/v1/wizard/respond",
                        json={"state": "angry", "severity": 8})
        assert "Cold" in r.json()["wizard_message"] or \
            r.json()["protocol"] == "Anger Reset"
        crisis = client.post("/api/v1/wizard/respond",
                             json={"state": "sad", "severity": 9,
                                   "message": "I want to end it all"})
        assert crisis.json()["crisis"] is True
        done = client.post("/api/v1/wizard/complete",
                           json={"name": "Cold Water on Wrists",
                                 "state": "angry", "severity_before": 8,
                                 "severity_after": 4, "effectiveness": 5})
        assert done.json()["ok"] is True

    def test_streams_and_misc(self, client):
        r = client.post("/api/v1/wizard/respond/stream",
                        json={"state": "stressed", "severity": 5})
        assert r.status_code == 200 and "text/event-stream" in r.headers[
            "content-type"]
        assert client.get("/api/v1/rhythm/morning").json()["mode"] \
            == "morning"
        assert client.get("/api/v1/rhythm/bogus").status_code == 404
        assert client.get("/api/v1/info").json()["name"] == "Motif"
