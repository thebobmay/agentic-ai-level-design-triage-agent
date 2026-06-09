"""Pydantic AI agents for the triage system.

Three agents do the judgment:

- The Intent Interpreter turns a natural language brief into a structured
  DesignIntentProfile and detects conflicts in the request itself.
- The Triage Director (optimizer, ReAct) calls the deterministic analysis tools
  for facts, reasons about intent versus facts and tradeoffs in context, and
  chooses one triage action with its narrative and any revision prescription.
- The Critic (evaluator, independent) judges whether the Director's recommendation
  is sound and constraint respecting, and can approve, send it back, or escalate.

The agents are grounded in the curated design knowledge. The model is set by
TRIAGE_MODEL (default openai-chat:gpt-4o-mini) at temperature 0. defer_model_check
lets the module import without credentials; tests override the model with TestModel.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import RunUsage

from src.design_knowledge import get_design_guidance
from src.models import (
    Critique,
    DesignIntentProfile,
    DifficultyResult,
    LevelFacts,
    NoveltyResult,
    PacingResult,
    SafeZoneResult,
    SpikeResult,
    TriageRecommendation,
    ValidationResult,
)
from src.tools import (
    ToolLog,
    analyze_candidate_pacing,
    detect_candidate_safe_zone,
    detect_candidate_spike,
    estimate_candidate_difficulty,
    measure_candidate_novelty,
    validate_candidate_level,
)

DEFAULT_MODEL = os.environ.get("TRIAGE_MODEL", "openai-chat:gpt-4o-mini")


# Intent Interpreter -----------------------------------------------------------

intent_interpreter = Agent(
    DEFAULT_MODEL,
    output_type=DesignIntentProfile,
    instructions=(
        "You interpret a designer's natural language brief for a 2D platformer level segment "
        "into a structured design intent. Infer the target audience, the desired feel, the "
        "difficulty target, the novelty preference, the hard constraints (non negotiable, such as "
        "preserve the core layout), and the soft preferences. Critically, detect conflicts within "
        "the brief itself, such as asking for beginner accessibility and intense hardcore challenge "
        "at once, and list them in detected_conflicts. If the brief is too vague to infer a target, "
        "choose a reasonable default and record the ambiguity in detected_conflicts. You only "
        "interpret the brief; you do not analyze the level."
    ),
    output_retries=2,
    defer_model_check=True,
)


def run_intent_interpreter(
    brief_text: str,
    model: str | None = None,
    model_settings: dict | None = None,
    usage: RunUsage | None = None,
) -> DesignIntentProfile:
    """Interpret a design brief into a structured intent profile."""
    prompt = f"Design brief:\n{brief_text}\n\nInterpret this brief into a design intent profile."
    return intent_interpreter.run_sync(
        prompt, model=model, model_settings=model_settings, usage=usage
    ).output


# Triage Director (optimizer) --------------------------------------------------

@dataclass
class DirectorDeps:
    """Injected dependencies for the Triage Director's tools."""

    candidate_level: str
    reference_levels: list[str]
    tool_log: ToolLog


triage_director = Agent(
    DEFAULT_MODEL,
    deps_type=DirectorDeps,
    output_type=TriageRecommendation,
    instructions=(
        "You are the Triage Director for 2D platformer level segments. You advise a human designer "
        "and you never edit the level. Work through your tools to gather facts (validity, difficulty, "
        "novelty, pacing, safe zone, difficulty spike); never guess these. Reason about how the "
        "candidate serves the interpreted intent, weighing tradeoffs in context. Choose exactly one "
        "action: accept_for_playtest when it is sound and on target (include playtest questions); "
        "recommend_revision when a diagnosed problem conflicts with the intent (provide a revision "
        "prescription of ordered, reasoned suggested edits that respect the hard constraints, plus a "
        "playtest question); request_clarification when the brief is too ambiguous or self "
        "conflicting to act on; flag_as_derivative_draft when novelty is low and the candidate may be "
        "derivative (usable as a draft, not final); reject_structural when the candidate is "
        "structurally invalid; request_human_review when signals conflict and need designer judgment. "
        "Only recommend revision to fix a real problem; accept a clean, on target level. Difficulty "
        "is heuristic, not player validated.\n\n" + get_design_guidance()
    ),
    output_retries=2,
    defer_model_check=True,
)


@triage_director.tool
def check_validity(ctx: RunContext[DirectorDeps]) -> ValidationResult:
    """Validate the candidate's structure, vocabulary, dimensions, and pipe integrity."""
    result = validate_candidate_level(ctx.deps.candidate_level)
    ctx.deps.tool_log.record("validate_candidate_level", {"level": "candidate"}, result)
    return result


@triage_director.tool
def check_difficulty(ctx: RunContext[DirectorDeps]) -> DifficultyResult:
    """Estimate the candidate's heuristic structural difficulty."""
    result = estimate_candidate_difficulty(ctx.deps.candidate_level)
    ctx.deps.tool_log.record("estimate_candidate_difficulty", {"level": "candidate"}, result)
    return result


@triage_director.tool
def check_novelty(ctx: RunContext[DirectorDeps]) -> NoveltyResult:
    """Measure the candidate's novelty against the reference library."""
    result = measure_candidate_novelty(ctx.deps.candidate_level, ctx.deps.reference_levels)
    ctx.deps.tool_log.record("measure_candidate_novelty", {"level": "candidate"}, result)
    return result


@triage_director.tool
def check_pacing(ctx: RunContext[DirectorDeps]) -> PacingResult:
    """Analyze the candidate's challenge pacing across the segment."""
    result = analyze_candidate_pacing(ctx.deps.candidate_level)
    ctx.deps.tool_log.record("analyze_candidate_pacing", {"level": "candidate"}, result)
    return result


@triage_director.tool
def check_safe_zone(ctx: RunContext[DirectorDeps]) -> SafeZoneResult:
    """Check whether the candidate opens with a safe zone before the first challenge."""
    result = detect_candidate_safe_zone(ctx.deps.candidate_level)
    ctx.deps.tool_log.record("detect_candidate_safe_zone", {"level": "candidate"}, result)
    return result


@triage_director.tool
def check_spike(ctx: RunContext[DirectorDeps]) -> SpikeResult:
    """Detect a localized difficulty spike (a gap combined with an enemy or cannon)."""
    result = detect_candidate_spike(ctx.deps.candidate_level)
    ctx.deps.tool_log.record("detect_candidate_spike", {"level": "candidate"}, result)
    return result


def run_triage_director(
    intent: DesignIntentProfile,
    candidate_level: str,
    reference_levels: list[str],
    tool_log: ToolLog,
    prior_feedback: list[str] | None = None,
    model: str | None = None,
    model_settings: dict | None = None,
    usage: RunUsage | None = None,
) -> TriageRecommendation:
    """Run the Triage Director over the candidate, optionally with prior critic feedback."""
    deps = DirectorDeps(
        candidate_level=candidate_level,
        reference_levels=reference_levels,
        tool_log=tool_log,
    )
    lines = [
        "Interpreted design intent:",
        intent.model_dump_json(indent=2),
        "",
        "Candidate level (14 rows by 32 columns):",
        candidate_level,
    ]
    if prior_feedback:
        lines += [
            "",
            "A critic returned your previous recommendation for revision. Address this feedback:",
            *[f"- {item}" for item in prior_feedback],
        ]
    lines += ["", "Gather facts with your tools, then choose one action and explain it."]
    return triage_director.run_sync(
        "\n".join(lines), deps=deps, model=model, model_settings=model_settings, usage=usage
    ).output


# Critic (evaluator) -----------------------------------------------------------

critic_agent = Agent(
    DEFAULT_MODEL,
    output_type=Critique,
    instructions=(
        "You are an independent design critic reviewing the Triage Director's recommendation for a "
        "2D platformer level segment. You see the interpreted intent, the gathered facts, and the "
        "recommendation. Judge whether the recommendation is sound: is the diagnosis consistent with "
        "the facts and the intent, are the hard constraints respected, and does the action over reach "
        "or under reach? Be skeptical; the Director is biased toward declaring success. Return "
        "verdict approve to finalize, revise to send it back with specific feedback (list "
        "remaining_issues and any constraint_violations), or escalate to require human review when "
        "the signals genuinely conflict. You never edit the level and never judge whether it is "
        "fun.\n\n" + get_design_guidance()
    ),
    output_retries=2,
    defer_model_check=True,
)


def run_critic(
    intent: DesignIntentProfile,
    candidate_level: str,
    facts: LevelFacts,
    recommendation: TriageRecommendation,
    model: str | None = None,
    model_settings: dict | None = None,
    usage: RunUsage | None = None,
) -> Critique:
    """Run the Critic to independently evaluate the Director's recommendation."""
    lines = [
        "Interpreted design intent:",
        intent.model_dump_json(indent=2),
        "",
        "Gathered facts:",
        facts.model_dump_json(indent=2),
        "",
        "Candidate level (14 rows by 32 columns):",
        candidate_level,
        "",
        "The Triage Director's recommendation:",
        recommendation.model_dump_json(indent=2),
        "",
        "Evaluate the recommendation and return your verdict.",
    ]
    return critic_agent.run_sync(
        "\n".join(lines), model=model, model_settings=model_settings, usage=usage
    ).output
