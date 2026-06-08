"""Deterministic analysis tools (facts only).

Report facts about a candidate level: structural validity, heuristic difficulty,
novelty and nearest neighbour similarity, pacing across the segment, an opening
safe zone, and localized difficulty spikes. These tools never decide and never
edit the level; they only measure.

Implemented in Phase 3.
"""

from __future__ import annotations
