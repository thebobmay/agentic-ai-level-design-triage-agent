"""Unit tests for src/scenarios.py and the hand authored level fixtures."""

from src.analysis_tools import estimate_difficulty, measure_novelty, validate_level
from src.level_io import get_level_dimensions
from src.models import ScenarioDefinition, TriageRequest
from src.reference_library import load_reference_levels
from src.scenarios import acceptable_actions, build_triage_request, load_candidate, load_scenarios

SCENARIOS = load_scenarios()
BY_ID = {s.scenario_id: s for s in SCENARIOS}


def test_seven_scenarios_load():
    assert len(SCENARIOS) == 7
    assert all(isinstance(s, ScenarioDefinition) for s in SCENARIOS)


def test_expected_actions_cover_the_intended_set():
    actions = {s.expected_action for s in SCENARIOS}
    assert actions == {
        "recommend_revision",
        "flag_as_derivative_draft",
        "request_clarification",
        "accept_for_playtest",
        "reject_structural",
    }


def test_every_candidate_loads_and_is_14_by_32():
    for scenario in SCENARIOS:
        level = load_candidate(scenario)
        assert get_level_dimensions(level) == (14, 32)


def test_build_triage_request_carries_brief_and_candidate():
    request = build_triage_request(BY_ID["S1"])
    assert isinstance(request, TriageRequest)
    assert request.brief_text
    assert request.candidate_level


# Fixture fact checks: the hand authored levels must exhibit the facts their scenarios need.

def test_s4_candidate_is_valid_and_easy():
    level = load_candidate(BY_ID["S4"])
    assert validate_level(level).is_valid
    assert estimate_difficulty(level).difficulty_label == "easy"


def test_s5_candidate_is_structurally_invalid():
    assert not validate_level(load_candidate(BY_ID["S5"])).is_valid


def test_s2_candidate_is_derivative_against_the_reference_library():
    refs = load_reference_levels()
    assert refs, "reference library should not be empty"
    result = measure_novelty(load_candidate(BY_ID["S2"]), refs)
    assert result.novelty_label == "low"


def test_s3_candidate_is_medium_difficulty():
    assert estimate_difficulty(load_candidate(BY_ID["S3"])).difficulty_label == "medium"


def test_acceptable_actions_includes_alternatives_and_falls_back():
    assert acceptable_actions(BY_ID["S3"]) == {"request_clarification", "request_human_review"}
    assert acceptable_actions(BY_ID["S4"]) == {"accept_for_playtest"}
