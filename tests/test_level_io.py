"""Unit tests for src/level_io.py."""

from src.level_io import (
    format_level,
    get_level_dimensions,
    load_level,
    parse_level,
    save_level,
)

SAMPLE = "----\n-XX-\nXXXX"


def test_parse_level_returns_rows_of_chars():
    grid = parse_level(SAMPLE)
    assert grid[0] == ["-", "-", "-", "-"]
    assert grid[1] == ["-", "X", "X", "-"]
    assert len(grid) == 3


def test_format_level_round_trips_with_parse():
    assert format_level(parse_level(SAMPLE)) == SAMPLE


def test_get_level_dimensions_returns_height_and_width():
    assert get_level_dimensions(SAMPLE) == (3, 4)


def test_get_level_dimensions_empty():
    assert get_level_dimensions("") == (1, 0)


def test_save_then_load_round_trips(tmp_path):
    path = tmp_path / "level.txt"
    save_level(SAMPLE, path)
    assert load_level(path) == SAMPLE


def test_load_trims_trailing_blank_lines(tmp_path):
    path = tmp_path / "level.txt"
    path.write_text(SAMPLE + "\n\n", encoding="utf-8")
    assert load_level(path) == SAMPLE
