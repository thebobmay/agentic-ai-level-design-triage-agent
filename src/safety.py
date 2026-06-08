"""The thin deterministic safety floor.

Enforces only hard facts and escalation over the agents' decision: a structurally
invalid candidate is never accepted or called ready, and an unresolved critic
dispute at the round cap escalates to human review. It never re decides the happy
path and never computes readiness from a metric.

Implemented in Phase 6.
"""

from __future__ import annotations
