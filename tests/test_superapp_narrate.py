"""Tier-2 narrator: grounded, sparse, honest about availability. No network."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

CARD = {
    "id": "rest",
    "title": "Rest & recovery",
    "tone": "attention",
    "finding": "Sleep has been running short — about 5.5h.",
    "proof": "sleep 7.2h then → 5.5h now",
    "meaning": "Sleep is your keystone; even thirty more minutes changes the day.",
}


class TestPromptGrounding:
    def test_facts_in_prompt(self):
        from superapp.intelligence import build_prompt

        prompt = build_prompt(
            CARD, "30",
            {"correlations": [{"metric_a": "sleep", "metric_b": "mood",
                               "r": 0.62, "n_days": 9}],
             "patterns": ["Stress averaging high."]})
        for fact in ("5.5h", "7.2h", "r=0.62", "last 30 days"):
            assert fact in prompt

    def test_system_bounds(self):
        from superapp.intelligence.narrate import SYSTEM

        lowered = SYSTEM.lower()
        assert "only the facts" in lowered
        assert "no diagnosis" in lowered or "diagnosis" in lowered


class TestAvailability:
    def test_no_key_means_unavailable_never_raise(self, monkeypatch):
        from superapp.intelligence import narrate

        for key in ("GROQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                    "OPENROUTER_API_KEY", "LIFE_OS_PROVIDER",
                    "LIFE_OS_MODEL"):
            monkeypatch.delenv(key, raising=False)
        result = narrate(CARD)
        assert result.get("unavailable") is True
        assert "GROQ_API_KEY" in result.get("reason", "")

    def test_empty_card_rejected_at_http(self):
        from fastapi.testclient import TestClient

        from superapp.surfaces.api import app

        c = TestClient(app)
        assert c.post("/api/v1/why", json={"card": {}}).status_code == 400

    def test_why_unavailable_over_http(self, monkeypatch):
        from fastapi.testclient import TestClient

        from superapp.surfaces.api import app

        for key in ("GROQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                    "OPENROUTER_API_KEY", "LIFE_OS_PROVIDER"):
            monkeypatch.delenv(key, raising=False)
        c = TestClient(app)
        r = c.post("/api/v1/why", json={"card": CARD})
        assert r.status_code == 200
        assert r.json().get("unavailable") is True
