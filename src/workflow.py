"""Triage orchestration.

`triage_candidate` runs the bounded evaluator-optimizer pass over a single
candidate: interpret the brief, gather authoritative facts, then loop the Triage
Director and Critic up to the round cap, apply the deterministic safety floor, and
return the full session. The agents decide and explain; the floor enforces only
facts and escalation. State and the tool call log are recorded for transparency.
"""

from __future__ import annotations

from pathlib import Path

from src.agents import run_critic, run_intent_interpreter, run_triage_director
from src.models import TriageRequest, TriageSession
from src.safety import MAX_ROUNDS, apply_safety_floor
from src.tools import ToolLog, gather_facts


def _critic_feedback(critique) -> list[str]:
    """Build the feedback list passed back to the Director for a revision round."""
    return critique.remaining_issues + critique.constraint_violations or [critique.assessment]


def triage_candidate(
    request: TriageRequest,
    reference_levels: list[str],
    max_rounds: int = MAX_ROUNDS,
) -> TriageSession:
    """Run the bounded triage pass and return the full session state."""
    state = TriageSession(brief_text=request.brief_text, candidate_level=request.candidate_level)
    log = ToolLog()

    # Agent 1: interpret the brief into structured intent.
    state.intent = run_intent_interpreter(request.brief_text)

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
        )
        state.recommendation = recommendation

        critique = run_critic(state.intent, request.candidate_level, facts, recommendation)
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
    return state


def save_audit_log(session: TriageSession, path: str | Path) -> None:
    """Persist the full session as a JSON audit log."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(session.model_dump_json(indent=2), encoding="utf-8")
