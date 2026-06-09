"""Run the triage workflow on a single candidate and persist its log.

Standalone entry point for the agentic system. Run a scenario from the suite, or
an ad hoc brief against a candidate level file. Prints the triage report, saves
the full session audit log, and appends a summary line to the running agent log
(outputs/logs/triage_runs.jsonl). Requires LLM credentials in .env.

Usage:
    python scripts/run_triage.py --scenario S1
    python scripts/run_triage.py --brief "beginner friendly opening" --candidate data/candidate_levels/candidate_s4.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=True)

from src.level_io import load_level
from src.models import TriageRequest
from src.reference_library import load_reference_levels
from src.report import generate_report
from src.scenarios import build_triage_request, load_scenarios
from src.workflow import append_run_log, save_audit_log, save_transcript, triage_candidate


def build_request(args: argparse.Namespace) -> tuple[str, TriageRequest]:
    """Build the triage request and a run label from the CLI arguments."""
    if args.scenario:
        scenarios = {s.scenario_id: s for s in load_scenarios()}
        if args.scenario not in scenarios:
            raise SystemExit(f"Unknown scenario id: {args.scenario}. Known: {', '.join(scenarios)}")
        scenario = scenarios[args.scenario]
        return scenario.scenario_id, build_triage_request(scenario)
    if not (args.brief and args.candidate):
        raise SystemExit("Provide --scenario, or both --brief and --candidate.")
    candidate = load_level(args.candidate)
    return Path(args.candidate).stem, TriageRequest(brief_text=args.brief, candidate_level=candidate)


def main() -> int:
    """Run one triage pass, print the report, and persist the logs."""
    parser = argparse.ArgumentParser(description="Run the triage agent on one candidate.")
    parser.add_argument("--scenario", help="Scenario id from data/scenarios.json (e.g. S1).")
    parser.add_argument("--brief", help="Ad hoc design brief text.")
    parser.add_argument("--candidate", help="Path to a candidate level file.")
    parser.add_argument("--logs-dir", default="outputs/logs", help="Directory for the audit log.")
    args = parser.parse_args()

    label, request = build_request(args)
    reference_levels = load_reference_levels()
    session = triage_candidate(request, reference_levels)

    print(generate_report(session))

    log_path = Path(args.logs_dir) / f"{label}.json"
    transcript_path = Path(args.logs_dir) / f"{label}_transcript.md"
    save_audit_log(session, log_path)
    save_transcript(session, transcript_path)
    append_run_log(session)
    print(f"\nDecision: {session.decision}  |  rounds: {session.round_count}")
    print(f"Audit log: {log_path}")
    print(f"Transcript: {transcript_path}")
    print("Running log: outputs/logs/triage_runs.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
