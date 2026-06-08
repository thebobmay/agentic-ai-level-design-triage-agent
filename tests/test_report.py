"""Unit tests for src/report.py (sessions built directly, no LLM)."""

from src.level_io import format_level
from src.models import (
    Critique,
    DesignIntentProfile,
    PrescribedEdit,
    RevisionPrescription,
    ToolCallLogEntry,
    TriageRecommendation,
    TriageSession,
)
from src.report import generate_report, save_report
from src.tools import gather_facts

W, H = 32, 14


def clean_level() -> str:
    rows = [["-"] * W for _ in range(H)]
    rows[H - 1] = ["X"] * W
    rows[H - 2] = ["X"] * W
    return format_level(rows)


def session(action, prescription=None) -> TriageSession:
    return TriageSession(
        brief_text="BRIEF MARKER",
        candidate_level=clean_level(),
        intent=DesignIntentProfile(
            target_audience="beginner", difficulty_target="easy", novelty_preference="medium"
        ),
        facts=gather_facts(clean_level(), []),
        recommendation=TriageRecommendation(
            action=action,
            diagnosis="DIAGNOSIS MARKER",
            tradeoff_reasoning=["a tradeoff"],
            prescription=prescription,
            playtest_readiness="ready_for_playtest",
            playtest_questions=["does the opening feel fair?"],
            confidence="moderate",
        ),
        critique=Critique(verdict="approve", assessment="CRITIC MARKER", confidence="moderate"),
        round_count=1,
        decision=action,
        tool_call_log=[ToolCallLogEntry(tool_name="validate_candidate_level", outputs={"is_valid": True})],
    )


def test_report_includes_agent_prose_and_facts():
    report = generate_report(session("accept_for_playtest"))
    assert "BRIEF MARKER" in report
    assert "DIAGNOSIS MARKER" in report  # the Director's prose, verbatim
    assert "CRITIC MARKER" in report  # the Critic's prose, verbatim
    assert "accept_for_playtest" in report
    assert "Difficulty: easy" in report  # the factual appendix
    assert "validate_candidate_level" in report  # the tool call log
    assert "Limitations" in report


def test_report_includes_prescription_when_revising():
    prescription = RevisionPrescription(
        suggested_edits=[PrescribedEdit(description="EDIT MARKER", reason="REASON MARKER")],
        playtest_question="QUESTION MARKER",
    )
    report = generate_report(session("recommend_revision", prescription))
    assert "Revision Prescription" in report
    assert "EDIT MARKER" in report
    assert "REASON MARKER" in report
    assert "QUESTION MARKER" in report


def test_report_omits_prescription_when_accepting():
    report = generate_report(session("accept_for_playtest"))
    assert "Revision Prescription" not in report


def test_save_report_writes_file(tmp_path):
    path = tmp_path / "report.md"
    save_report(generate_report(session("accept_for_playtest")), path)
    assert path.exists()
    assert "Triage Report" in path.read_text(encoding="utf-8")
