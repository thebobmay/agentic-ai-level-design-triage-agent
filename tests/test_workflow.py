"""Integration tests for the bounded evaluator-optimizer workflow.

All three agents are overridden with Pydantic AI TestModel (no API key) so the
pass runs deterministically. These assert the loop behavior and the safety floor
invariants, not exact narrative.
"""

from contextlib import ExitStack

from pydantic_ai.models.test import TestModel

from src.agents import critic_agent, intent_interpreter, triage_director
from src.safety import MAX_ROUNDS
from src.scenarios import build_triage_request, load_scenarios
from src.workflow import save_audit_log, triage_candidate

BY_ID = {s.scenario_id: s for s in load_scenarios()}

INTENT_ARGS = {
    "target_audience": "beginner",
    "desired_feel": ["approachable"],
    "difficulty_target": "easy",
    "novelty_preference": "medium",
    "hard_constraints": [],
    "soft_preferences": [],
    "detected_conflicts": [],
}


def controlled(action="accept_for_playtest", readiness="ready_for_playtest", verdict="approve") -> ExitStack:
    """Override all three agents with controlled TestModels."""
    interp = TestModel(custom_output_args=INTENT_ARGS)
    director = TestModel(
        custom_output_args={
            "action": action,
            "diagnosis": "diagnosis",
            "tradeoff_reasoning": ["reason"],
            "prescription": None,
            "playtest_readiness": readiness,
            "playtest_questions": ["q"],
            "confidence": "moderate",
        }
    )
    critic = TestModel(
        custom_output_args={
            "verdict": verdict,
            "remaining_issues": ["needs work"] if verdict == "revise" else [],
            "constraint_violations": [],
            "assessment": "assessment",
            "confidence": "moderate",
        }
    )
    stack = ExitStack()
    stack.enter_context(intent_interpreter.override(model=interp))
    stack.enter_context(triage_director.override(model=director))
    stack.enter_context(critic_agent.override(model=critic))
    return stack


def run(scenario_id, **kwargs):
    request = build_triage_request(BY_ID[scenario_id])
    with controlled(**kwargs):
        return triage_candidate(request, [])


def test_invalid_candidate_is_rejected_regardless_of_proposal():
    state = run("S5", action="accept_for_playtest", verdict="approve")
    assert state.decision == "reject_structural"
    assert state.recommendation.playtest_readiness == "not_ready"


def test_clean_candidate_accepted_when_critic_approves():
    state = run("S4", action="accept_for_playtest", verdict="approve")
    assert state.decision == "accept_for_playtest"
    assert state.round_count == 1


def test_persistent_dispute_hits_cap_and_escalates():
    state = run("S4", action="recommend_revision", readiness="revise_before_playtest", verdict="revise")
    assert state.round_count == MAX_ROUNDS
    assert state.decision == "request_human_review"
    assert state.critic_feedback_history  # feedback flowed across rounds


def test_critic_escalation_breaks_immediately():
    state = run("S4", action="accept_for_playtest", verdict="escalate")
    assert state.decision == "request_human_review"
    assert state.round_count == 1


def test_session_records_intent_facts_and_tool_log():
    state = run("S4")
    assert state.intent is not None
    assert state.facts is not None and state.facts.validation.is_valid
    assert state.tool_call_log  # the director's tool calls were logged


def test_save_audit_log_writes_json(tmp_path):
    state = run("S4")
    path = tmp_path / "audit.json"
    save_audit_log(state, path)
    assert path.exists()
    assert "brief_text" in path.read_text(encoding="utf-8")
