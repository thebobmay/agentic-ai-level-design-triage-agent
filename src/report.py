"""Report assembly.

Assembles the designer facing triage report from agent authored prose (the
Director's narrative and the Critic's assessment) plus a deterministic factual
appendix (exact metrics, tool call log, the level grid). It generates no prose of
its own, so reported numbers are ground truth rather than hallucinated.

Implemented in Phase 10.
"""

from __future__ import annotations
