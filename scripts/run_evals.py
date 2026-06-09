"""Run the pydantic-evals scenario suite against the real agents and save the report.

Runs every scenario through the triage workflow, evaluates the invariants and
properties, and writes a rendered report to outputs/eval_results/eval_report.txt
as a committed record. Requires LLM credentials in .env. Set EVAL_LLM_JUDGE=1 to
also run the optional LLM judge.

Usage:
    python scripts/run_evals.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=True)

from src.evals import run_eval_suite
from src.reference_library import load_reference_levels

OUTPUT_PATH = ROOT / "outputs" / "eval_results" / "eval_report.txt"


def main() -> int:
    """Run the eval suite, save the rendered report, and print an ASCII summary."""
    report = run_eval_suite(load_reference_levels())
    rendered = report.render(width=120, include_reasons=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rendered, encoding="utf-8")

    averages = report.averages()
    # Print an ASCII summary; the full table with box characters is in the saved file
    # (the Windows console encoding cannot render those characters).
    print(f"Saved eval report to {OUTPUT_PATH}")
    print(f"Cases: {len(report.cases)}")
    print(f"Invariant assertions passing: {averages.assertions:.0%}")
    for name, score in averages.scores.items():
        print(f"Score {name}: {score:.3f}")
    return 0 if averages.assertions == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
