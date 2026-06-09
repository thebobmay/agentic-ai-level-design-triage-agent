"""Unit tests for src/prompts.py and the prompt templates."""

from src.prompts import PROMPT_VARIANT, load_prompt

AGENTS = ("intent_interpreter", "triage_director", "critic")


def test_default_variant_is_tuned():
    assert PROMPT_VARIANT == "tuned"


def test_both_variants_load_for_every_agent():
    for variant in ("baseline", "tuned"):
        for name in AGENTS:
            assert load_prompt(name, variant=variant).strip()


def test_tuning_changed_the_interpreter_and_director():
    assert load_prompt("intent_interpreter", "tuned") != load_prompt("intent_interpreter", "baseline")
    assert load_prompt("triage_director", "tuned") != load_prompt("triage_director", "baseline")


def test_tuned_director_encodes_the_precedence_rules():
    text = load_prompt("triage_director", "tuned")
    assert "structurally invalid" in text
    assert "request_clarification" in text
    assert "detected_conflicts" in text
