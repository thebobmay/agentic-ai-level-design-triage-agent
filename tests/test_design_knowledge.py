"""Unit tests for src/design_knowledge.py."""

from src.design_knowledge import DESIGN_GUIDANCE, get_design_guidance


def test_guidance_is_non_empty():
    assert get_design_guidance().strip()
    assert get_design_guidance() == DESIGN_GUIDANCE


def test_guidance_covers_the_core_principles():
    text = get_design_guidance().lower()
    for anchor in ("intent", "safe zone", "derivative", "playtest", "never edit"):
        assert anchor in text


def test_guidance_states_pacing_is_target_relative():
    text = get_design_guidance().lower()
    assert "relative to the target" in text
    assert "accept it for playtest" in text  # the accept when clean rule
