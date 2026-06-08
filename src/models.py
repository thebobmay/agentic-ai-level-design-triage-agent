"""Pydantic schemas and session state for the triage agent.

Defines the typed contracts that flow through the system: the design intent
profile, the deterministic fact result models, the triage recommendation and the
revision prescription, the critic's verdict, the session state that serves as
working memory, and the terminal triage action set.

Implemented in Phase 1.
"""

from __future__ import annotations
