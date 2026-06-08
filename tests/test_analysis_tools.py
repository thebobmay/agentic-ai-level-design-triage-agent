"""Unit tests for src/analysis_tools.py."""

from src.analysis_tools import (
    analyze_pacing,
    detect_difficulty_spike,
    detect_safe_zone,
    estimate_difficulty,
    measure_novelty,
    tile_similarity,
    validate_level,
)
from src.level_io import format_level

W, H = 32, 14


def base_rows() -> list[list[str]]:
    """A valid clean level: air over two ground rows."""
    rows = [["-"] * W for _ in range(H)]
    rows[H - 1] = ["X"] * W
    rows[H - 2] = ["X"] * W
    return rows


def text(rows: list[list[str]]) -> str:
    return format_level(rows)


# Validation

def test_clean_level_is_valid():
    result = validate_level(text(base_rows()))
    assert result.is_valid
    assert result.fatal_errors == []


def test_invalid_tile_is_fatal():
    rows = base_rows()
    rows[5][5] = "Z"
    result = validate_level(text(rows))
    assert not result.is_valid
    assert any("invalid tile" in e for e in result.fatal_errors)


def test_wrong_dimensions_is_fatal():
    small = "\n".join("-" * 10 for _ in range(10))
    result = validate_level(small)
    assert not result.is_valid
    assert any("expected 14 by 32" in e for e in result.fatal_errors)


def test_valid_pipe_passes():
    rows = base_rows()
    rows[H - 3][10] = "<"
    rows[H - 3][11] = ">"  # pipe top resting on the ground row below
    assert validate_level(text(rows)).is_valid


def test_orphan_pipe_top_is_fatal():
    rows = base_rows()
    rows[8][10] = "<"
    rows[8][11] = ">"  # air directly beneath
    result = validate_level(text(rows))
    assert not result.is_valid
    assert any("without a body or ground" in e for e in result.fatal_errors)


def test_unmatched_pipe_half_is_fatal():
    rows = base_rows()
    rows[H - 3][10] = "<"  # no matching '>' to the right
    result = validate_level(text(rows))
    assert not result.is_valid
    assert any("matching pipe top right" in e for e in result.fatal_errors)


# Difficulty

def test_difficulty_easy_for_clean_flat_level():
    assert estimate_difficulty(text(base_rows())).difficulty_label == "easy"


def test_difficulty_medium_for_moderate_gap():
    rows = base_rows()
    for c in (5, 6, 7):  # a 3 wide pit
        rows[H - 1][c] = "-"
        rows[H - 2][c] = "-"
    result = estimate_difficulty(text(rows))
    assert result.longest_gap == 3
    assert result.difficulty_label == "medium"


def test_difficulty_hard_for_large_gap():
    rows = base_rows()
    for c in range(5, 10):  # a 5 wide pit
        rows[H - 1][c] = "-"
        rows[H - 2][c] = "-"
    assert estimate_difficulty(text(rows)).difficulty_label == "hard"


# Novelty

def test_identical_level_is_low_novelty():
    level = text(base_rows())
    result = measure_novelty(level, [level])
    assert result.nearest_neighbor_similarity == 1.0
    assert result.novelty_label == "low"
    assert result.warning is not None


def test_distinct_level_is_more_novel():
    rows = base_rows()
    other = base_rows()
    for c in range(0, W, 2):  # change many cells
        other[6][c] = "E"
        other[8][c] = "o"
    result = measure_novelty(text(rows), [text(other)])
    assert result.nearest_neighbor_similarity < 1.0
    assert result.novelty_label in ("medium", "high")


def test_empty_reference_library_is_high_novelty():
    result = measure_novelty(text(base_rows()), [])
    assert result.nearest_neighbor_similarity == 0.0
    assert result.novelty_label == "high"


def test_tile_similarity_identical_is_one():
    level = text(base_rows())
    assert tile_similarity(level, level) == 1.0


# Pacing

def test_pacing_flat_for_clean_level():
    assert analyze_pacing(text(base_rows())).flag == "flat"


def test_pacing_front_loaded_when_challenge_is_early():
    rows = base_rows()
    for c in (2, 3, 4):
        rows[H - 3][c] = "E"
    profile = analyze_pacing(text(rows))
    assert profile.flag == "front_loaded"
    assert profile.opening_intensity > profile.final_intensity


def test_pacing_back_loaded_when_challenge_is_late():
    rows = base_rows()
    for c in (27, 28, 29):
        rows[H - 3][c] = "E"
    assert analyze_pacing(text(rows)).flag == "back_loaded"


# Safe zone

def test_safe_zone_present_when_opening_is_clear():
    rows = base_rows()
    rows[H - 3][20] = "E"  # first challenge late
    result = detect_safe_zone(text(rows))
    assert result.has_opening_safe_zone
    assert result.first_challenge_column == 20


def test_safe_zone_absent_when_challenge_is_immediate():
    rows = base_rows()
    rows[H - 1][1] = "-"  # a gap at column 1
    result = detect_safe_zone(text(rows))
    assert not result.has_opening_safe_zone
    assert result.first_challenge_column == 1


# Difficulty spike

def test_spike_detected_for_gap_plus_enemy():
    rows = base_rows()
    rows[H - 1][10] = "-"
    rows[H - 1][11] = "-"  # a 2 wide gap
    rows[H - 3][12] = "E"  # an enemy within the window
    assert detect_difficulty_spike(text(rows)).has_spike


def test_no_spike_for_clean_level():
    assert not detect_difficulty_spike(text(base_rows())).has_spike
