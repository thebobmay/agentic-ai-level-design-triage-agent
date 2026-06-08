"""Unit tests for src/reference_library.py."""

from src.reference_library import load_reference_levels


def test_loads_txt_files_sorted(tmp_path):
    (tmp_path / "b.txt").write_text("BBBB", encoding="utf-8")
    (tmp_path / "a.txt").write_text("AAAA", encoding="utf-8")
    levels = load_reference_levels(tmp_path)
    assert levels == ["AAAA", "BBBB"]


def test_empty_directory_returns_empty_list(tmp_path):
    assert load_reference_levels(tmp_path) == []
