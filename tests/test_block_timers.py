from __future__ import annotations

import random
from dataclasses import dataclass

from blocks import Block
from runtime.block_timers import update_block_timers


@dataclass
class _FakeEnemy:
    pos: tuple[int, int]


def test_update_block_timers_leaves_unexpired_block_in_place() -> None:
    maze = [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
    ]
    blocks = [Block(pos=(1, 1), expires_at=200)]
    blocked_set: set[tuple[int, int]] = set()

    update_block_timers(
        blocks=blocks,
        blocked_set=blocked_set,
        player_pos=(0, 0),
        goal=(2, 2),
        enemies=[],
        maze=maze,
        rng=random.Random(1),
        now_ms=100,
        block_lifetime_ms=4000,
    )

    assert blocks[0].pos == (1, 1)
    assert blocks[0].expires_at == 200
    assert blocked_set == {(1, 1)}


def test_update_block_timers_respawns_expired_block_and_resets_expiration() -> None:
    maze = [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1],
    ]
    blocks = [Block(pos=(1, 1), expires_at=100)]
    blocked_set: set[tuple[int, int]] = set()

    update_block_timers(
        blocks=blocks,
        blocked_set=blocked_set,
        player_pos=(1, 1),
        goal=(2, 2),
        enemies=[],
        maze=maze,
        rng=random.Random(1),
        now_ms=100,
        block_lifetime_ms=4000,
    )

    assert blocks[0].pos in {(1, 2), (1, 3)}
    assert blocks[0].expires_at == 4100
    assert blocked_set == {blocks[0].pos}


def test_update_block_timers_avoids_player_goal_enemy_and_other_block_positions() -> None:
    maze = [
        [1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1],
    ]
    expired_block = Block(pos=(1, 1), expires_at=50)
    other_block = Block(pos=(1, 2), expires_at=999)
    blocks = [expired_block, other_block]
    blocked_set: set[tuple[int, int]] = set()
    enemies = [_FakeEnemy(pos=(1, 3))]

    update_block_timers(
        blocks=blocks,
        blocked_set=blocked_set,
        player_pos=(1, 4),
        goal=(0, 0),
        enemies=enemies,
        maze=maze,
        rng=random.Random(7),
        now_ms=100,
        block_lifetime_ms=2500,
    )

    assert expired_block.pos not in {(1, 2), (1, 3), (1, 4)}
    assert expired_block.pos == (1, 1)
    assert blocked_set == {(1, 1), (1, 2)}


def test_update_block_timers_only_respawns_expired_block_when_multiple_blocks_exist() -> None:
    maze = [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1],
    ]
    expired_block = Block(pos=(1, 1), expires_at=100)
    stable_block = Block(pos=(1, 2), expires_at=10_000)
    blocks = [expired_block, stable_block]
    blocked_set: set[tuple[int, int]] = set()

    update_block_timers(
        blocks=blocks,
        blocked_set=blocked_set,
        player_pos=(1, 1),
        goal=(2, 2),
        enemies=[],
        maze=maze,
        rng=random.Random(2),
        now_ms=100,
        block_lifetime_ms=5000,
    )

    assert stable_block.pos == (1, 2)
    assert stable_block.expires_at == 10_000
    assert expired_block.pos == (1, 3)
    assert expired_block.expires_at == 5100
    assert blocked_set == {(1, 2), (1, 3)}
