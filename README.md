# AI Level Design Triage Agent

**Student:** Robert Mayfield

An advisory, multi agent AI workflow that triages a single 2D platformer level candidate against a designer's natural language brief. Given a brief and one candidate level, the system interprets the designer's intent, gathers factual evidence with deterministic analysis tools, reasons about the design tradeoffs, and recommends the next design action. It does not generate levels, does not edit levels, and does not claim a level is objectively fun. Its job is to support a human designer's next decision.

The governing principle is that deterministic code owns facts and hard safety, while the language model agents own judgment, decision, and explanation. The tools measure level properties; the agents interpret messy human intent, decide which facts matter in context, weigh the tradeoffs, and produce the recommendation. The output is advisory and human in the loop: the designer chooses whether to apply it, and every change to the level is made by the designer.

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
- `data/reference_levels/` — a small set of hand authored reference levels in a Super Mario Bros tile vocabulary, used by the novelty tool to measure similarity.

All candidate and reference levels were hand authored for this project as 14 row by 32 column text segments, with a tile vocabulary inspired by the Super Mario Bros levels in the Video Game Level Corpus (Summerville et al., 2016) rather than taken from it. The repository is self contained and does not depend on any prior project artifact.

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

Deterministic code stays deliberately thin. The analysis tools (validity, difficulty, novelty, pacing, safe zone, difficulty spike) report facts only and never decide. The safety floor enforces only the hard rules: a structurally invalid candidate is rejected for structural reasons and never called ready, request_clarification is forced to not_ready, and a critic escalation or an unresolved dispute at the round cap escalates to human review; it never converts one valid agent action into another. Working memory carries the brief, intent, the evolving recommendation, the critic's feedback, and the round counter through the pass, and a separate audit log persists every tool call, each agent's output, the round by round critic verdicts, the full transcript, and the final decision. The report contains no machine generated prose of its own; it lays out the agents' narrative and appends a factual appendix so reported numbers are ground truth.

The full diagram is in `architecture_diagram.png` (source in `architecture_diagram.md`).

# Requirements

- Python 3.11 or newer.
- An OpenAI compatible API key for the agent calls (the system is model agnostic via `TRIAGE_MODEL`; gpt-4.1 was selected by the model comparison experiment).
- The Python dependencies in `requirements.txt`: `pydantic-ai`, `pydantic`, `pydantic-evals`, `numpy`, `pandas`, `matplotlib`, `jupyter`, `pytest`, `python-dotenv`, and `nest-asyncio`.

The test suite runs offline with Pydantic AI TestModel, so no API key is needed to verify the implementation.

# References

Summerville, A., Snodgrass, S., Mateas, M., & Ontañón, S. (2016). The VGLC: The video game level corpus. *Proceedings of the 7th Workshop on Procedural Content Generation.* arXiv:1606.07487. [https://arxiv.org/abs/1606.07487](https://arxiv.org/abs/1606.07487)