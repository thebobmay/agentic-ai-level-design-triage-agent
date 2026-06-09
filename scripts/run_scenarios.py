"""Run the full scenario suite against the real agents and save its artifacts.

Runs each scenario through the triage workflow, writes a triage report per
scenario to outputs/reports/, an audit log per scenario to outputs/logs/, and a
results table to outputs/scenario_results.csv. Requires LLM credentials in .env.

Usage:
    python scripts/run_scenarios.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=True)

from src.reference_library import load_reference_levels
from src.scenarios import load_scenarios
from src.workflow import run_scenario_suite


def main() -> int:
    """Run the suite and print a one line summary per scenario."""
    reference_levels = load_reference_levels()
    results = run_scenario_suite(load_scenarios(), reference_levels)

    matches = sum(1 for result in results if result.match_expected)
    for result in results:
        status = "OK" if result.match_expected else "DIFF"
        print(f"{result.scenario_id} {result.actual_action:<24} {status} ({result.name})")
    print(f"\n{matches}/{len(results)} scenarios matched their expected action.")
    print("Reports in outputs/reports/, logs in outputs/logs/, summary in outputs/scenario_results.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
