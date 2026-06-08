"""Unit tests for src/models.py (schema contracts, no LLM)."""

from typing import get_args

import pytest
from pydantic import ValidationError

from src.models import (
    Critique,
    DesignIntentProfile,
    PrescribedEdit,
    RevisionPrescription,
    TriageAction,
    TriageRecommendation,
    TriageSession,
)

EXPECTED_ACTIONS = {
    "accept_for_playtest",
    "recommend_revision",
    "request_clarification",
    "flag_as_derivative_draft",
    "reject_structural",
    "request_human_review",
}


def test_triage_action_set_is_exactly_the_six_terminal_actions():
    assert set(get_args(TriageAction)) == EXPECTED_ACTIONS


def test_intent_profile_requires_core_fields_and_defaults_lists():
    intent = DesignIntentProfile(
        target_audience="beginner",
        difficulty_target="easy",
        novelty_preference="medium",
    )
    assert intent.hard_constraints == []
    assert intent.detected_conflicts == []


def test_recommendation_can_carry_a_prescription():
    rec = TriageRecommendation(
        action="recommend_revision",
        diagnosis="Enemy sits near the first jump.",
        playtest_readiness="revise_before_playtest",
        confidence="moderate",
        prescription=RevisionPrescription(
            suggested_edits=[PrescribedEdit(description="Move the enemy later", reason="Reduce a local spike")],
            playtest_question="Did the first jump feel fair?",
        ),
    )
    assert rec.prescription is not None
    assert rec.prescription.suggested_edits[0].reason


def test_recommendation_rejects_unknown_action():
    with pytest.raises(ValidationError):
        TriageRecommendation(
            action="delete_level",
            diagnosis="x",
            playtest_readiness="not_ready",
            confidence="low",
        )


def test_session_defaults_are_sensible():
    session = TriageSession(brief_text="make it beginner friendly", candidate_level="...")
    assert session.round_count == 1
    assert session.decision is None
    assert session.tool_call_log == []
    assert session.critic_feedback_history == []


def test_critique_verdict_is_constrained():
    critique = Critique(verdict="approve", assessment="looks sound", confidence="high")
    assert critique.verdict == "approve"
    with pytest.raises(ValidationError):
        Critique(verdict="maybe", assessment="x", confidence="low")
