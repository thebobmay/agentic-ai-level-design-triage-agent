"""Evaluation suite.

A pydantic-evals dataset built from the scenarios. Because the triage action is a
judgment under interpreted intent, it asserts invariants and required properties
rather than exact action equality, and records exact agreement as a score. An
optional LLM judge is gated behind an env flag so the suite runs offline by
default.

Implemented in Phase 11.
"""

from __future__ import annotations
