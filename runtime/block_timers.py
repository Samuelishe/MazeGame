from __future__ import annotations

"""Runtime-facing helper for block expiration and respawn updates."""

import random
from typing import Protocol

from blocks import Block, respawn_block

Coord = tuple[int, int]


class _EnemyLike(Protocol):
    pos: Coord


def update_block_timers(
    *,
    blocks: list[Block],
    blocked_set: set[Coord],
    player_pos: Coord,
    goal: Coord,
    enemies: list[_EnemyLike],
    maze: list[list[int]],
    rng: random.Random,
    now_ms: int,
    block_lifetime_ms: int,
) -> None:
    """Обновляет истекшие блоки и пересобирает blocked_set in-place."""
    blocked_set.clear()
    blocked_set.update(block.pos for block in blocks)

    for block in blocks:
        if now_ms < block.expires_at:
            continue

        forbidden_dynamic = {
            player_pos,
            goal,
            *(enemy.pos for enemy in enemies),
            *(other.pos for other in blocks if other is not block),
        }
        respawn_block(block, maze, rng, forbidden_dynamic)
        block.expires_at = now_ms + block_lifetime_ms

        blocked_set.clear()
        blocked_set.update(other.pos for other in blocks)
