"""Pydantic AI agents for the triage system.

Three agents do the judgment. The Intent Interpreter turns a natural language
brief into a structured intent profile and detects conflicts in the request. The
Triage Director (optimizer, ReAct) calls the analysis tools for facts, reasons
about intent versus facts and tradeoffs, chooses a triage action, and authors the
design direction narrative. The Critic (evaluator, independent) judges soundness
and constraint adherence and can approve, send back for revision, or escalate.

Implemented in Phase 8.
"""

from __future__ import annotations
