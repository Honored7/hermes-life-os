"""Tests for the wizard (LLM mocked — tests logic, not model output)."""

import pytest
from unittest.mock import patch, MagicMock
from wellness.wizard import Wizard
from wellness.interventions import INTERVENTIONS


@pytest.fixture
def wizard():
    """Wizard with mocked LLM (no actual model calls)."""
    with patch("wellness.wizard.resolve_provider", return_value="ollama"), \
         patch("wellness.wizard.get_client", return_value=MagicMock()), \
         patch("wellness.wizard.default_model_for", return_value="test-model"):
        w = Wizard()
        # Mock _generate to return None (forces template fallback)
        w._generate = MagicMock(return_value=None)
        return w


@pytest.fixture
def wizard_with_llm():
    """Wizard with mocked LLM that returns a canned response."""
    with patch("wellness.wizard.resolve_provider", return_value="ollama"), \
         patch("wellness.wizard.get_client", return_value=MagicMock()), \
         patch("wellness.wizard.default_model_for", return_value="test-model"):
        w = Wizard()
        w._generate = MagicMock(return_value="I hear you. That sounds really hard. Want to try breathing together?")
        return w


class TestWizardRespond:
    """Test respond_to_state()."""

    def test_returns_wizard_message(self, wizard):
        result = wizard.respond_to_state("stressed", severity=6)
        assert "wizard_message" in result
        assert len(result["wizard_message"]) > 0

    def test_returns_intervention(self, wizard):
        result = wizard.respond_to_state("stressed", severity=6)
        assert result["intervention"] is not None
        assert "id" in result["intervention"]
        assert "name" in result["intervention"]
        assert "steps" in result["intervention"]

    def test_returns_session_config(self, wizard):
        result = wizard.respond_to_state("stressed", severity=6)
        assert result["session_config"] is not None
        assert "intervention_id" in result["session_config"]

    def test_high_severity_triggers_protocol(self, wizard):
        result = wizard.respond_to_state("angry", severity=9)
        assert result["protocol"] is not None
        assert result["protocol"]["name"] == "Anger Reset"
        assert result["protocol"]["total_steps"] == 4

    def test_good_mood_celebration(self, wizard):
        result = wizard.respond_to_state("good", severity=8)
        assert result["intervention"]["name"] == "Win Celebration"

    def test_llm_response_used_when_available(self, wizard_with_llm):
        result = wizard_with_llm.respond_to_state("stressed", severity=6)
        assert result["llm_used"] is True
        assert "I hear you" in result["wizard_message"]

    def test_template_fallback_when_llm_fails(self, wizard):
        result = wizard.respond_to_state("stressed", severity=6)
        assert result["llm_used"] is False
        # Should use the intervention's wizard_intro
        iv_id = result["intervention"]["id"]
        assert result["wizard_message"] == INTERVENTIONS[iv_id].wizard_intro

    def test_alternatives_provided(self, wizard):
        result = wizard.respond_to_state("stressed", severity=6)
        assert "alternatives" in result


class TestWizardChat:
    """Test free-form chat."""

    def test_chat_returns_message(self, wizard):
        result = wizard.chat("I feel terrible today")
        assert "wizard_message" in result
        assert len(result["wizard_message"]) > 0

    def test_chat_with_llm(self, wizard_with_llm):
        result = wizard_with_llm.chat("I feel terrible today")
        assert result["llm_used"] is True


class TestWizardCelebrate:
    """Test win celebration."""

    def test_celebrate_returns_message(self, wizard):
        result = wizard.celebrate_win("Finished my project!")
        assert "wizard_message" in result
        assert result["intervention"]["name"] == "Win Celebration"


class TestWizardComplete:
    """Test post-intervention check-in."""

    def test_complete_returns_message(self, wizard):
        result = wizard.complete_intervention(
            intervention_id=1, state="stressed",
            severity_before=7, severity_after=4,
            effectiveness_rating=4,
        )
        assert "wizard_message" in result

    def test_complete_invalid_intervention(self, wizard):
        result = wizard.complete_intervention(
            intervention_id=999, state="stressed", severity_before=7,
        )
        assert "wizard_message" in result


class TestWizardStatus:
    """Test status reporting."""

    def test_status(self, wizard):
        status = wizard.status()
        assert status["llm_provider"] == "ollama"
        assert status["interventions"] == 24
        assert status["engine"] == "active"


class TestSessionConfig:
    """Test breathing animation configs."""

    def test_478_breathing_pattern(self, wizard):
        result = wizard.respond_to_state("stressed", severity=8)
        config = result.get("session_config")
        if config and config.get("breathing_pattern"):
            bp = config["breathing_pattern"]
            assert bp["inhale"] == 4
            assert bp["hold_in"] == 7
            assert bp["exhale"] == 8

    def test_box_breathing_pattern(self, wizard):
        # Force box breathing by using a context that prefers it
        iv = INTERVENTIONS[2]  # Box Breathing
        config = wizard._session_config(iv)
        assert config["breathing_pattern"]["inhale"] == 4
        assert config["breathing_pattern"]["hold_in"] == 4
        assert config["breathing_pattern"]["exhale"] == 4
        assert config["breathing_pattern"]["hold_out"] == 4
