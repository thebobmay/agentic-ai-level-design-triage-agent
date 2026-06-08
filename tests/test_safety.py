"""Unit tests for src/safety.py."""

from src.level_io import format_level
from src.models import Critique, TriageRecommendation
from src.safety import MAX_ROUNDS, apply_safety_floor
from src.tools import gather_facts

W, H = 32, 14


def clean_level() -> str:
    rows = [["-"] * W for _ in range(H)]
    rows[H - 1] = ["X"] * W
    rows[H - 2] = ["X"] * W
    return format_level(rows)


def invalid_level() -> str:
    rows = [["-"] * W for _ in range(H)]
    rows[H - 1] = ["X"] * W
    rows[H - 2] = ["X"] * W
    rows[5][5] = "Z"  # invalid tile
    return format_level(rows)


VALID_FACTS = gather_facts(clean_level(), [])
INVALID_FACTS = gather_facts(invalid_level(), [])


def rec(action, readiness="ready_for_playtest") -> TriageRecommendation:
    return TriageRecommendation(
        action=action,
        diagnosis="d",
        playtest_readiness=readiness,
        confidence="moderate",
    )


def critique(verdict) -> Critique:
    return Critique(verdict=verdict, assessment="a", confidence="moderate")


def test_clean_approved_accept_is_unchanged():
    out = apply_safety_floor(rec("accept_for_playtest"), VALID_FACTS, critique("approve"), 1)
    assert out.action == "accept_for_playtest"
    assert out.readiness == "ready_for_playtest"
    assert out.interventions == []


def test_invalid_candidate_cannot_be_accepted():
    out = apply_safety_floor(rec("accept_for_playtest"), INVALID_FACTS, critique("approve"), 1)
    assert out.action == "reject_structural"
    assert out.readiness == "not_ready"


def test_invalid_candidate_is_never_ready_even_for_other_actions():
    out = apply_safety_floor(
        rec("recommend_revision", readiness="ready_for_playtest"), INVALID_FACTS, critique("approve"), 1
    )
    assert out.readiness == "not_ready"


def test_critic_escalation_forces_human_review():
    out = apply_safety_floor(rec("accept_for_playtest"), VALID_FACTS, critique("escalate"), 1)
    assert out.action == "request_human_review"
    assert out.readiness != "ready_for_playtest"


def test_unresolved_dispute_at_cap_escalates():
    out = apply_safety_floor(rec("recommend_revision"), VALID_FACTS, critique("revise"), MAX_ROUNDS)
    assert out.action == "request_human_review"


def test_dispute_before_cap_does_not_escalate():
    out = apply_safety_floor(rec("recommend_revision", readiness="revise_before_playtest"),
                             VALID_FACTS, critique("revise"), MAX_ROUNDS - 1)
    assert out.action == "recommend_revision"
