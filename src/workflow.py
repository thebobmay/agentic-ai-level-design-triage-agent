"""Triage orchestration.

`triage_candidate` runs the bounded evaluator-optimizer pass over a single
candidate: interpret the brief, gather authoritative facts, then loop the Triage
Director and Critic up to the round cap, apply the deterministic safety floor, and
return the full session. The agents decide and explain; the floor enforces only
facts and escalation. State and the tool call log are recorded for transparency.
"""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic_ai.usage import RunUsage

from src.agents import run_critic, run_intent_interpreter, run_triage_director
from src.models import (
    ScenarioDefinition,
    ScenarioResult,
    TokenUsage,
    TriageRequest,
    TriageSession,
)
from src.report import generate_report, save_report
from src.safety import MAX_ROUNDS, apply_safety_floor
from src.scenarios import acceptable_actions, build_triage_request
from src.tools import ToolLog, gather_facts


_DEFAULT_MODEL_SETTINGS = {"temperature": 0.0}


def _critic_feedback(critique) -> list[str]:
    """Build the feedback list passed back to the Director for a revision round."""
    return critique.remaining_issues + critique.constraint_violations or [critique.assessment]


def triage_candidate(
    request: TriageRequest,
    reference_levels: list[str],
    max_rounds: int = MAX_ROUNDS,
    model: str | None = None,
    model_settings: dict | None = _DEFAULT_MODEL_SETTINGS,
) -> TriageSession:
    """Run the bounded triage pass and return the full session state.

    `model` and `model_settings` override the agents per run, so the model
    selection experiment can run the same pass under different models (chat models
    pass a temperature; reasoning models pass model_settings=None).
    """
    state = TriageSession(brief_text=request.brief_text, candidate_level=request.candidate_level)
    log = ToolLog()
    usage = RunUsage()

    # Agent 1: interpret the brief into structured intent.
    state.intent = run_intent_interpreter(
        request.brief_text, model=model, model_settings=model_settings, usage=usage
    )

    # Authoritative facts, independent of the Director's own tool calls, for the
    # critic and the safety floor.
    facts = gather_facts(request.candidate_level, reference_levels)
    state.facts = facts

    # Evaluator-optimizer loop: Director proposes, Critic evaluates, up to the cap.
    for round_num in range(1, max_rounds + 1):
        state.round_count = round_num
        recommendation = run_triage_director(
            state.intent,
            request.candidate_level,
            reference_levels,
            log,
            prior_feedback=state.critic_feedback_history or None,
            model=model,
            model_settings=model_settings,
            usage=usage,
        )
        state.recommendation = recommendation

        critique = run_critic(
            state.intent,
            request.candidate_level,
            facts,
            recommendation,
            model=model,
            model_settings=model_settings,
            usage=usage,
        )
        state.critique = critique

        if critique.verdict in ("approve", "escalate"):
            break
        if round_num >= max_rounds:
            break
        state.critic_feedback_history.extend(_critic_feedback(critique))

    # Deterministic safety floor over the agents' result.
    outcome = apply_safety_floor(state.recommendation, facts, state.critique, state.round_count)
    state.decision = outcome.action
    state.recommendation.playtest_readiness = outcome.readiness
    if outcome.interventions:
        log.record(
            "safety_floor",
            {"round_count": state.round_count},
            {"final_action": outcome.action, "interventions": outcome.interventions},
        )

    state.tool_call_log = log.entries
    state.token_usage = TokenUsage(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
        requests=usage.requests,
    )
    return state


def save_audit_log(session: TriageSession, path: str | Path) -> None:
    """Persist the full session as a JSON audit log."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(session.model_dump_json(indent=2), encoding="utf-8")


_CSV_FIELDS = [
    "scenario_id",
    "name",
    "expected_action",
    "actual_action",
    "readiness",
    "match_expected",
    "rounds",
    "key_reason",
]


def _key_reason(session: TriageSession) -> str:
    """Pick the most meaningful driving reason for the scenario summary."""
    if session.facts and session.facts.validation.fatal_errors:
        return session.facts.validation.fatal_errors[0]
    if session.intent and session.intent.detected_conflicts:
        return session.intent.detected_conflicts[0]
    return session.decision or "unknown"


def _write_scenario_csv(results: list[ScenarioResult], csv_path: str | Path) -> None:
    """Write the scenario results to a CSV file."""
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for result in results:
            writer.writerow(result.model_dump())


def run_scenario_suite(
    scenarios: list[ScenarioDefinition],
    reference_levels: list[str],
    reports_dir: str | Path = "outputs/reports",
    logs_dir: str | Path = "outputs/logs",
    csv_path: str | Path = "outputs/scenario_results.csv",
    model: str | None = None,
    model_settings: dict | None = _DEFAULT_MODEL_SETTINGS,
) -> list[ScenarioResult]:
    """Run every scenario through the workflow, save reports, logs, and a results CSV."""
    results: list[ScenarioResult] = []
    for scenario in scenarios:
        session = triage_candidate(
            build_triage_request(scenario),
            reference_levels,
            model=model,
            model_settings=model_settings,
        )
        save_report(generate_report(session), Path(reports_dir) / f"{scenario.scenario_id}.md")
        save_audit_log(session, Path(logs_dir) / f"{scenario.scenario_id}.json")
        rec = session.recommendation
        results.append(
            ScenarioResult(
                scenario_id=scenario.scenario_id,
                name=scenario.name,
                expected_action=scenario.expected_action,
                actual_action=session.decision or "request_human_review",
                readiness=rec.playtest_readiness if rec else "not_ready",
                match_expected=(session.decision in acceptable_actions(scenario)),
                rounds=session.round_count,
                key_reason=_key_reason(session),
            )
        )
    _write_scenario_csv(results, csv_path)
    return results
