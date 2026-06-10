# AI Level Design Triage Agent

**Student:** Robert Mayfield

An advisory, human in the loop agentic system that triages a single 2D platformer level candidate against a designer's natural language brief. Given a brief and one candidate level, the system interprets the designer's intent, gathers facts with deterministic tools, reasons about the tradeoffs in context, and recommends the next design action. It never edits the level. The designer makes every change.

The governing principle keeps the agent honest: deterministic code owns facts and safety, and the language model owns judgment, decision, and explanation. Every component is held to one test. If the agent were removed and only the tools remained, what is lost? Here the answer is intent interpretation, contextual tradeoff reasoning, conflict detection, the triage decision, the revision prescription, and human review escalation.

# Project Description

The system is a design direction layer. It runs one bounded pass over a single candidate. Three Pydantic AI agents do the judgment:

- **Intent Interpreter** reads the free text brief and infers a structured design intent (audience, desired feel, difficulty and novelty targets, hard constraints, soft preferences), and detects conflicts or vagueness in the request itself.
- **Triage Director** is a ReAct agent. It calls the deterministic analysis tools for facts, reasons about intent versus facts and the tradeoffs in this specific context, chooses one triage action, and authors the design direction narrative, including a revision prescription when it recommends revision.
- **Critic** independently re examines the candidate, the intent, and the facts against the Director's recommendation. It can approve, send the recommendation back to the Director for revision, or escalate to human review.

The Director and the Critic form a bounded evaluator-optimizer loop with a hard cap of five rounds. A thin deterministic safety floor enforces only hard facts and escalation. The terminal action is one of six: accept for playtest, recommend revision, request clarification, flag as derivative draft, reject for structural reasons, or request human review.

# Dataset and Inputs

This project does not train a model. It consumes natural language design briefs, candidate levels, and a small reference library:

- `data/scenarios.json` — seven natural language design briefs, each paired with a candidate level and the expected triage behavior, used for evaluation.
- `data/candidate_levels/` — seven hand authored candidate 2D platformer level segments used by the scenarios.
- `data/reference_levels/` — a small set of hand authored reference levels written in the VGLC Super Mario Bros tile format, used by the novelty tool to measure similarity.

All candidate and reference levels are hand authored for this project. They use the Super Mario Bros tile vocabulary from the Video Game Level Corpus (Summerville et al., 2016) in 14 row by 32 column text segments. The repository is self contained and does not depend on any prior project artifact.

# Files Included

```
agentic_system.ipynb        # executable system demonstration and scenario harness
architecture_diagram.md     # Mermaid source for the architecture diagram
architecture_diagram.png    # rendered architecture diagram
README.md
requirements.txt
.env.example
prompt_templates/           # baseline and tuned agent prompts, swappable by variant
scripts/                    # run_triage, run_scenarios, run_evals, run_tests
src/                        # the implementation package (see Architecture Overview)
data/                       # scenarios, candidate levels, reference library
outputs/                    # logs, reports, eval results, figures, test results
reports/                    # the report PDFs
tests/                      # pytest suite
```

The `src/` package holds the system: `models.py` (Pydantic schemas and state), `level_io.py`, `analysis_tools.py`, `reference_library.py`, `design_knowledge.py`, `tools.py`, `prompts.py`, `agents.py`, `safety.py`, `workflow.py`, `scenarios.py`, `report.py`, `evals.py`, and `model_config.py`.

# How to Run

1. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   pip install -r requirements.txt
   ```

2. Provide credentials. Copy `.env.example` to `.env` and set your key:

   ```bash
   OPENAI_API_KEY=your_key_here
   TRIAGE_MODEL=openai-chat:gpt-4.1
   ```

3. Run the system. Any of the following work:

   ```bash
   # One triage pass, on a built in scenario or your own brief and candidate
   python scripts/run_triage.py --scenario S1
   python scripts/run_triage.py --brief "A beginner friendly opening" --candidate data/candidate_levels/candidate_s4_playtest_ready.txt

   # The full scenario demonstration suite (reports, logs, transcripts, summary)
   python scripts/run_scenarios.py

   # The invariant based evaluation suite
   python scripts/run_evals.py

   # The test suite (offline, no API key required; uses Pydantic AI TestModel)
   python scripts/run_tests.py
   ```

   Or open `agentic_system.ipynb` and run it top to bottom for the full narrative demonstration, model comparison, tuning validation, scenario suite, and evaluation.

Each live run prints the triage report and saves an audit log and a readable transcript to `outputs/logs/`, plus a line in the running log `outputs/logs/triage_runs.jsonl`. The test suite runs without credentials.

# Architecture Overview

```text
Natural language brief + candidate level
        |
1. Intent Interpreter  ->  DesignIntentProfile (+ detected conflicts)
        |
2. Triage Director (optimizer, ReAct)
   calls deterministic tools for facts, reasons intent vs facts and tradeoffs,
   chooses one triage action, authors the design direction narrative
        |
3. Critic (evaluator, independent)
   approve   -> safety floor -> report
   dispute   -> back to the Director (bounded loop, cap 5 rounds)
   exhausted -> escalate to human review
```

Deterministic code stays deliberately thin. The analysis tools (validity, difficulty, novelty, pacing, safe zone, difficulty spike) report facts only and never decide. The safety floor enforces only that a structurally invalid candidate is never accepted or called ready and that an unresolved critic dispute escalates to human review; it never converts one valid agent action into another. Working memory carries the brief, intent, the evolving recommendation, the critic's feedback, and the round counter through the pass, and a separate audit log persists every tool call, each agent's output, the round by round critic verdicts, the full transcript, and the final decision. The report contains no machine generated prose of its own; it lays out the agents' narrative and appends a factual appendix so reported numbers are ground truth.

The full diagram is in `architecture_diagram.png` (source in `architecture_diagram.md`).

# Bias and Responsible Use

This system is advisory and bounded, and its limits are stated plainly:

- **It never edits the level.** Every change is made by the human designer. The system surfaces evidence and a recommended next step and preserves creative control.
- **Difficulty is a structural heuristic, not player validated difficulty.** Every report discloses this caveat. The system never claims a level is objectively fun.
- **Novelty is relative to a small curated reference library.** A low novelty or high similarity result means similar to that library, not globally derivative, so it is reported as a flag for the designer rather than a verdict.
- **Language model reasoning is non deterministic.** Evaluation therefore relies on invariants and scenario behavior rather than exact action matching, and the model identifier and temperature are pinned for reproducibility.
- **Conflicting or ambiguous briefs are escalated, not guessed.** The interpreter surfaces conflicts and vagueness, and the Director requests clarification rather than inventing a target.
- **Accountability stays with the human.** The safety floor and the bounded loop constrain the agents, the audit log records the full reasoning trace, and an unresolved dispute escalates to human review.

# Future Integration Reflection

## How this agent supports the AI Game Director Studio

This agent is the design direction layer of the larger AI Game Director Studio vision. Its public entry point, `triage_candidate(request)`, takes a brief and one candidate and returns a full triage session. In the integrated studio it is the component that decides what to do with a candidate: whether to accept it for playtest, prescribe a revision for the designer, flag it as derivative, or send it back. Because the bounded evaluator-optimizer loop that refines the advice lives inside the agent, the studio can reuse the agent unchanged.

## How the system would need to evolve for deeper integration

Deeper integration is the outer product loop, reserved for the next project. It would generate several candidate drafts, run each through this agent, rank the triaged candidates, fold in playtester feedback, and iterate the design across rounds. The agent itself would not be redesigned. The reference library would grow so that novelty is measured against a richer baseline, and the design knowledge would expand. The studio would add candidate generation and a feedback interpreter around the agent rather than changing how it triages.

## How agentic automation could assist this workflow

Agentic automation lets the studio move from one candidate at a time to a managed design loop while keeping the designer in control. The agent reads messy human intent, gathers evidence with tools, and produces a defensible recommendation with a concrete revision prescription, which is exactly the repetitive, evidence gathering part of level direction that benefits from automation. The human stays the decision maker. The agent advises, logs its full reasoning for review, and escalates when signals conflict, so automation increases throughput and consistency without removing creative authority.

# Requirements

- Python 3.11 or newer.
- An OpenAI compatible API key for the agent calls (the system is model agnostic via `TRIAGE_MODEL`; gpt-4.1 was selected by the model comparison experiment).
- The Python dependencies in `requirements.txt`: `pydantic-ai`, `pydantic`, `pydantic-evals`, `numpy`, `pandas`, `matplotlib`, `jupyter`, `pytest`, `python-dotenv`, and `nest-asyncio`.

The test suite runs offline with Pydantic AI TestModel, so no API key is needed to verify the implementation.

# References

Summerville, A., Snodgrass, S., Mateas, M., & Ontañón, S. (2016). The VGLC: The video game level corpus. *Proceedings of the 7th Workshop on Procedural Content Generation.* arXiv:1606.07487. [https://arxiv.org/abs/1606.07487](https://arxiv.org/abs/1606.07487)
