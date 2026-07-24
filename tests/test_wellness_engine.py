"""Tests for the wellness recommendation engine."""

import pytest
from wellness.engine import WellnessEngine, Recommendation, EngineResult
from wellness.interventions import INTERVENTIONS


@pytest.fixture
def engine():
    return WellnessEngine()


class TestRecommendation:
    """Test the core recommend() method."""

    def test_returns_engine_result(self, engine):
        result = engine.recommend("stressed", severity=5)
        assert isinstance(result, EngineResult)
        assert len(result.recommendations) > 0

    def test_respects_limit(self, engine):
        result = engine.recommend("stressed", severity=5, limit=2)
        assert len(result.recommendations) <= 2

    def test_stressed_returns_relevant(self, engine):
        result = engine.recommend("stressed", severity=7)
        names = {r.intervention.name for r in result.recommendations}
        # At severity 7, should include breathwork or immediate interventions
        assert len(names) > 0

    def test_angry_high_severity_triggers_protocol(self, engine):
        result = engine.recommend("angry", severity=9)
        assert result.protocol is not None
        assert result.protocol.id == "anger_reset"

    def test_angry_low_severity_no_protocol(self, engine):
        result = engine.recommend("angry", severity=4)
        assert result.protocol is None

    def test_good_mood_returns_celebration(self, engine):
        result = engine.recommend("good", severity=8)
        assert result.recommendations[0].intervention.name == "Win Celebration"

    def test_unknown_state_returns_empty(self, engine):
        result = engine.recommend("nonexistent", severity=5)
        assert len(result.recommendations) == 0

    def test_context_filters_infeasible(self, engine):
        # Can't go outside → should not recommend Cooldown Walk or Nature Time
        result = engine.recommend(
            "angry", severity=5,
            context={"can_go_outside": False},
        )
        names = {r.intervention.name for r in result.recommendations}
        assert "Cooldown Walk" not in names

    def test_work_context_prefers_discreet(self, engine):
        result = engine.recommend(
            "stressed", severity=6,
            context={"location": "work", "time_available_min": 3},
        )
        # Should prefer quick, discreet interventions
        top = result.recommendations[0]
        assert top.intervention.duration_seconds <= 300

    def test_recommendations_sorted_by_score(self, engine):
        result = engine.recommend("stressed", severity=6)
        scores = [r.score for r in result.recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_wizard_context_populated(self, engine):
        result = engine.recommend("sad", severity=5)
        assert result.wizard_context["state"] == "sad"
        assert result.wizard_context["severity"] == 5


class TestScoring:
    """Test the scoring logic."""

    def test_high_severity_prefers_immediate(self, engine):
        result = engine.recommend("angry", severity=9,
                                  context={"can_go_outside": False})
        # Cold Water (immediate) should score high at severity 9
        names = [r.intervention.name for r in result.recommendations]
        assert "Cold Water on Wrists" in names

    def test_contraindication_filters(self, engine):
        # Body Scan has contraindication "active_panic_attack"
        result = engine.recommend(
            "anxious", severity=6,
            context={"conditions": ["active_panic_attack"]},
        )
        names = {r.intervention.name for r in result.recommendations}
        assert "Body Scan" not in names


class TestProtocols:
    """Test protocol triggering."""

    def test_anxiety_protocol_at_7(self, engine):
        result = engine.recommend("anxious", severity=7)
        assert result.protocol is not None
        assert result.protocol.id == "anxiety_spiral"

    def test_overwhelm_protocol_at_8(self, engine):
        result = engine.recommend("overwhelmed", severity=8)
        assert result.protocol is not None
        assert result.protocol.id == "overwhelm_reset"

    def test_sadness_protocol_at_6(self, engine):
        result = engine.recommend("sad", severity=6)
        assert result.protocol is not None
        assert result.protocol.id == "sadness_support"

    def test_low_energy_protocol_at_5(self, engine):
        result = engine.recommend("low_energy", severity=5)
        assert result.protocol is not None
        assert result.protocol.id == "low_energy_reboot"

    def test_loneliness_protocol_at_6(self, engine):
        result = engine.recommend("lonely", severity=6)
        assert result.protocol is not None
        assert result.protocol.id == "loneliness_bridge"

    def test_no_protocol_below_threshold(self, engine):
        result = engine.recommend("anxious", severity=5)
        assert result.protocol is None
