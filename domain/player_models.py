"""Pure player domain models for Maze Game."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PlayerAggregateStats:
    """
    Aggregated per-player statistics stored in ``player_stats``.

    This is a pure data model with no repository or runtime behavior.
    """

    best_score: int = 0
    best_time_ms: Optional[int] = None
    max_coins: int = 0
    total_runs: int = 0
    wins: int = 0
    deaths: int = 0
    total_time_ms: int = 0
    total_coins: int = 0
    bronze_total: int = 0
    silver_total: int = 0
    gold_total: int = 0
    diamond_total: int = 0


@dataclass
class PlayerProfile:
    """
    Player identity plus optional aggregated statistics.

    This is a pure domain model with no persistence behavior.
    """

    player_id: int
    name: str
    stats: Optional[PlayerAggregateStats] = None
