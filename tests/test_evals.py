"""Tests for the pydantic-evals scenario suite (offline, TestModel).

Both the agents are overridden with TestModel (no API key, no spend). The suite
must build, run every scenario, and satisfy every invariant assertion regardless
of the stubbed agent behavior. That is the point of the safety floor and the
invariants: the workflow stays consistent even when the agent proposal is
degenerate. The exact expected action is recorded as a score, not asserted.
"""

from contextlib import ExitStack

from pydantic_ai.models.test import TestModel

from src.agents import critic_agent, intent_interpreter, triage_director
from src.evals import build_dataset, run_eval_suite
from src.reference_library import load_reference_levels

REFS = load_reference_levels()

INTENT_ARGS = {
    "target_audience": "beginner",
    "desired_feel": ["approachable"],
    "difficulty_target": "easy",
    "novelty_preference": "medium",
    "hard_constraints": [],
    "soft_preferences": [],
    "detected_conflicts": [],
}


def controlled() -> ExitStack:
    """Override all three agents with controlled TestModels."""
    interp = TestModel(custom_output_args=INTENT_ARGS)
    director = TestModel(
        custom_output_args={
            "action": "accept_for_playtest",
            "diagnosis": "diagnosis",
            "tradeoff_reasoning": ["reason"],
            "prescription": None,
            "playtest_readiness": "ready_for_playtest",
            "playtest_questions": ["q"],
            "confidence": "moderate",
        }
    )
    critic = TestModel(
        custom_output_args={
            "verdict": "approve",
            "remaining_issues": [],
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


def test_dataset_has_a_case_per_scenario_and_no_judge_by_default():
    dataset = build_dataset()
    assert len(dataset.cases) == 7
    evaluator_names = {type(e).__name__ for e in dataset.evaluators}
    assert "LLMJudge" not in evaluator_names  # gated off without EVAL_LLM_JUDGE
    assert "SafetyInvariants" in evaluator_names


def test_all_invariants_hold_under_stubbed_agents():
    with controlled():
        report = run_eval_suite(REFS)
    assert len(report.cases) == 7
    assert report.averages().assertions == 1.0


def test_expected_action_match_is_recorded_as_a_score():
    with controlled():
        report = run_eval_suite(REFS)
    assert "ExpectedActionMatch" in report.averages().scores
