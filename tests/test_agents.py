"""Tests for src/agents.py using Pydantic AI TestModel (no API key, no spend)."""

from pydantic_ai.models.test import TestModel

from src.agents import (
    DEFAULT_MODEL,
    critic_agent,
    intent_interpreter,
    run_critic,
    run_intent_interpreter,
    run_triage_director,
    triage_director,
)
from src.level_io import format_level
from src.models import Critique, DesignIntentProfile, TriageRecommendation
from src.tools import ToolLog, gather_facts

W, H = 32, 14

INTENT_ARGS = {
    "target_audience": "beginner",
    "desired_feel": ["approachable"],
    "difficulty_target": "easy",
    "novelty_preference": "medium",
    "hard_constraints": [],
    "soft_preferences": [],
    "detected_conflicts": [],
}
REC_ARGS = {
    "action": "accept_for_playtest",
    "diagnosis": "Sound and on target.",
    "tradeoff_reasoning": ["meets the easy target"],
    "prescription": None,
    "playtest_readiness": "ready_for_playtest",
    "playtest_questions": ["Does the opening feel fair?"],
    "confidence": "moderate",
}
CRITIQUE_ARGS = {
    "verdict": "approve",
    "remaining_issues": [],
    "constraint_violations": [],
    "assessment": "The recommendation is consistent with the facts.",
    "confidence": "moderate",
}


def clean_level() -> str:
    rows = [["-"] * W for _ in range(H)]
    rows[H - 1] = ["X"] * W
    rows[H - 2] = ["X"] * W
    return format_level(rows)


def test_module_imports_without_credentials():
    assert DEFAULT_MODEL


def test_intent_interpreter_returns_profile():
    with intent_interpreter.override(model=TestModel(custom_output_args=INTENT_ARGS)):
        intent = run_intent_interpreter("a beginner friendly opening")
    assert isinstance(intent, DesignIntentProfile)
    assert intent.difficulty_target == "easy"


def test_director_returns_recommendation_and_logs_tool_calls():
    log = ToolLog()
    intent = DesignIntentProfile(**INTENT_ARGS)
    with triage_director.override(model=TestModel(custom_output_args=REC_ARGS)):
        rec = run_triage_director(intent, clean_level(), [], log)
    assert isinstance(rec, TriageRecommendation)
    assert rec.action == "accept_for_playtest"
    assert log.entries, "the director should have called and logged its tools"


def test_critic_returns_critique():
    intent = DesignIntentProfile(**INTENT_ARGS)
    facts = gather_facts(clean_level(), [])
    rec = TriageRecommendation(**REC_ARGS)
    with critic_agent.override(model=TestModel(custom_output_args=CRITIQUE_ARGS)):
        critique = run_critic(intent, clean_level(), facts, rec)
    assert isinstance(critique, Critique)
    assert critique.verdict == "approve"
