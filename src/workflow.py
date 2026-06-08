"""Triage orchestration.

`triage_candidate` runs the bounded evaluator-optimizer pass over a single
candidate: interpret intent, then loop the Triage Director and Critic up to the
round cap, apply the deterministic safety floor, assemble the report, and persist
the audit log. The agents decide and explain; the floor enforces only facts and
escalation.

Implemented in Phase 9.
"""

from __future__ import annotations
