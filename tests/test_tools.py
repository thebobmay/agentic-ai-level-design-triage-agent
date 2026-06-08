"""Unit tests for src/tools.py."""

from src.level_io import format_level
from src.models import (
    DifficultyResult,
    LevelFacts,
    ValidationResult,
)
from src.tools import (
    TOOL_REGISTRY,
    ToolLog,
    estimate_candidate_difficulty,
    gather_facts,
    validate_candidate_level,
)

W, H = 32, 14


def clean_level() -> str:
    rows = [["-"] * W for _ in range(H)]
    rows[H - 1] = ["X"] * W
    rows[H - 2] = ["X"] * W
    return format_level(rows)


def test_wrappers_return_typed_results():
    level = clean_level()
    assert isinstance(validate_candidate_level(level), ValidationResult)
    assert isinstance(estimate_candidate_difficulty(level), DifficultyResult)


def test_gather_facts_populates_every_field():
    facts = gather_facts(clean_level(), [])
    assert isinstance(facts, LevelFacts)
    assert facts.validation.is_valid
    assert facts.difficulty.difficulty_label == "easy"
    assert facts.pacing.flag == "flat"


def test_tool_registry_lists_the_six_tools():
    names = {entry["tool"] for entry in TOOL_REGISTRY}
    assert len(TOOL_REGISTRY) == 6
    assert "validate_candidate_level" in names
    assert all("purpose" in entry for entry in TOOL_REGISTRY)


def test_tool_log_records_calls_with_serialized_output():
    log = ToolLog()
    result = validate_candidate_level(clean_level())
    log.record("validate_candidate_level", {"level": "candidate"}, result)
    assert len(log.entries) == 1
    entry = log.entries[0]
    assert entry.tool_name == "validate_candidate_level"
    assert entry.outputs["is_valid"] is True
