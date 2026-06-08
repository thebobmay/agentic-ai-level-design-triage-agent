"""Agent facing tool registry and tool call logging.

Wraps the deterministic analysis tools as the agent facing tool layer, exposes a
registry for the notebook, and records every tool call (inputs and outputs) into
the session for the audit log.

Implemented in Phase 5.
"""

from __future__ import annotations
