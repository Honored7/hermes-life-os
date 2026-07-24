"""Tests for the 24 wellness interventions."""

import pytest
from wellness.interventions import (
    INTERVENTIONS, Intervention, InterventionFamily, InterventionFormat,
    InterventionIntensity, EmotionalState,
    get_intervention, get_by_state, get_by_family, get_all,
)


class TestInterventionData:
    """Verify data integrity of all 24 interventions."""

    def test_all_24_loaded(self):
        assert len(INTERVENTIONS) == 24

    def test_ids_are_sequential(self):
        ids = sorted(INTERVENTIONS.keys())
        assert ids == list(range(1, 25))

    def test_every_intervention_has_required_fields(self):
        for iv in INTERVENTIONS.values():
            assert iv.name, f"ID {iv.id}: missing name"
            assert iv.description, f"ID {iv.id}: missing description"
            assert len(iv.states) > 0, f"ID {iv.id}: no states"
            assert iv.severity_range[0] <= iv.severity_range[1], f"ID {iv.id}: bad severity range"
            assert iv.duration_seconds > 0, f"ID {iv.id}: bad duration"
            assert len(iv.steps) > 0, f"ID {iv.id}: no steps"
            assert iv.wizard_intro, f"ID {iv.id}: no wizard_intro"
            assert iv.wizard_outro, f"ID {iv.id}: no wizard_outro"

    def test_severity_ranges_valid(self):
        for iv in INTERVENTIONS.values():
            lo, hi = iv.severity_range
            assert 1 <= lo <= 10, f"ID {iv.id}: severity min {lo} out of range"
            assert 1 <= hi <= 10, f"ID {iv.id}: severity max {hi} out of range"

    def test_all_families_used(self):
        families = {iv.family for iv in INTERVENTIONS.values()}
        assert InterventionFamily.BREATHWORK in families
        assert InterventionFamily.MOVEMENT in families
        assert InterventionFamily.CELEBRATION in families
        assert InterventionFamily.PREPARATION in families

    def test_all_formats_valid(self):
        for iv in INTERVENTIONS.values():
            assert isinstance(iv.format, InterventionFormat)

    def test_all_states_valid(self):
        valid = {s.value for s in EmotionalState}
        for iv in INTERVENTIONS.values():
            for s in iv.states:
                assert s.value in valid, f"ID {iv.id}: invalid state {s}"


class TestInterventionQueries:
    """Test query helpers."""

    def test_get_intervention_by_id(self):
        iv = get_intervention(1)
        assert iv is not None
        assert iv.name == "4-7-8 Breathing"

    def test_get_intervention_missing(self):
        assert get_intervention(999) is None

    def test_get_by_state_stressed(self):
        results = get_by_state("stressed")
        assert len(results) >= 5
        names = {iv.name for iv in results}
        assert "Box Breathing" in names
        assert "Meditation" in names

    def test_get_by_state_angry(self):
        results = get_by_state("angry")
        names = {iv.name for iv in results}
        assert "Cold Water on Wrists" in names
        assert "Cooldown Walk" in names

    def test_get_by_state_good(self):
        results = get_by_state("good")
        assert len(results) == 1
        assert results[0].name == "Win Celebration"

    def test_get_by_state_unknown(self):
        results = get_by_state("nonexistent_state")
        assert results == []

    def test_get_by_family(self):
        results = get_by_family(InterventionFamily.BREATHWORK)
        assert len(results) == 2  # 4-7-8 + Box Breathing
        for iv in results:
            assert iv.family == InterventionFamily.BREATHWORK

    def test_get_all_returns_24(self):
        assert len(get_all()) == 24

    def test_get_all_sorted_by_id(self):
        all_iv = get_all()
        ids = [iv.id for iv in all_iv]
        assert ids == sorted(ids)


class TestInterventionMatching:
    """Test the matching methods on Intervention."""

    def test_matches_state(self):
        iv = get_intervention(1)  # 4-7-8 Breathing
        assert iv.matches_state("angry")
        assert iv.matches_state("stressed")
        assert not iv.matches_state("lonely")

    def test_matches_severity(self):
        iv = get_intervention(1)  # severity (5, 10)
        assert iv.matches_severity(5)
        assert iv.matches_severity(10)
        assert not iv.matches_severity(3)

    def test_is_feasible_no_constraints(self):
        iv = get_intervention(1)  # requires nothing
        assert iv.is_feasible({})

    def test_is_feasible_needs_outside(self):
        iv = get_intervention(4)  # Cooldown Walk, requires outside
        assert iv.is_feasible({"can_go_outside": True})
        assert not iv.is_feasible({"can_go_outside": False})

    def test_is_feasible_time_constraint(self):
        iv = get_intervention(7)  # Body Scan, 300 seconds = 5 min
        assert iv.is_feasible({"time_available_min": 10})
        assert not iv.is_feasible({"time_available_min": 2})
