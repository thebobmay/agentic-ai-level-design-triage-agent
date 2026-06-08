"""Run the pytest suite and store result artifacts.

Executes pytest and writes two committed artifacts under outputs/test_results/:
pytest_report.txt (full console output with a run timestamp, command, and exit
code) and pytest_results.xml (JUnit results). Regenerate after adding or changing
tests and commit the refreshed report alongside the change.

Usage:
    python scripts/run_tests.py
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "outputs" / "test_results"


def main() -> int:
    """Run pytest, save the console report and JUnit XML, and return the exit code."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    xml_path = RESULTS_DIR / "pytest_results.xml"
    report_path = RESULTS_DIR / "pytest_report.txt"

    command = [sys.executable, "-m", "pytest", "-q", f"--junitxml={xml_path}"]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    output = completed.stdout + completed.stderr

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    header = (
        f"Run: {timestamp}\n"
        f"Command: {' '.join(command)}\n"
        f"Exit code: {completed.returncode}\n"
        + "=" * 70
        + "\n"
    )
    report_path.write_text(header + output, encoding="utf-8")

    print(output)
    print(f"Saved report to {report_path}")
    print(f"Saved JUnit XML to {xml_path}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
