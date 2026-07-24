"""Tests for the 6 chained protocols."""

import pytest
from wellness.protocols import PROTOCOLS, get_protocol, get_all_protocols, Protocol
from wellness.interventions import INTERVENTIONS


class TestProtocolData:
    """Verify protocol data integrity."""

    def test_six_protocols_loaded(self):
        assert len(PROTOCOLS) == 6

    def test_all_protocols_have_steps(self):
        for p in PROTOCOLS.values():
            assert len(p.steps) >= 3, f"{p.id}: too few steps"

    def test_all_protocols_end_with_check_in(self):
        for p in PROTOCOLS.values():
            assert p.steps[-1].is_check_in, f"{p.id}: last step should be check-in"

    def test_all_intervention_ids_valid(self):
        for p in PROTOCOLS.values():
            for step in p.steps:
                if step.intervention_id is not None:
                    assert step.intervention_id in INTERVENTIONS, \
                        f"{p.id}: invalid intervention_id {step.intervention_id}"

    def test_all_steps_have_wizard_messages(self):
        for p in PROTOCOLS.values():
            for i, step in enumerate(p.steps):
                assert step.wizard_message, f"{p.id} step {i}: missing wizard_message"

    def test_total_duration_positive(self):
        for p in PROTOCOLS.values():
            assert p.total_duration_seconds >= 0


class TestProtocolMatching:
    """Test protocol triggering logic."""

    def test_anger_reset_triggers(self):
        p = get_protocol("angry", 7)
        assert p is not None
        assert p.id == "anger_reset"

    def test_anger_reset_not_below_threshold(self):
        p = get_protocol("angry", 6)
        assert p is None

    def test_anxiety_spiral_triggers(self):
        p = get_protocol("anxious", 8)
        assert p is not None
        assert p.id == "anxiety_spiral"

    def test_no_protocol_for_good_mood(self):
        p = get_protocol("good", 10)
        assert p is None

    def test_no_protocol_for_unknown_state(self):
        p = get_protocol("nonexistent", 10)
        assert p is None

    def test_get_all_protocols(self):
        all_p = get_all_protocols()
        assert len(all_p) == 6

    def test_protocol_matches_method(self):
        p = PROTOCOLS["anger_reset"]
        assert p.matches("angry", 7)
        assert p.matches("angry", 10)
        assert not p.matches("angry", 5)
        assert not p.matches("sad", 9)
