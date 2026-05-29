from __future__ import annotations

import random

from enemies import Enemy, EnemyType
from runtime.enemy_updates import update_enemies


def _make_enemy(*, pos=(1, 1), next_step_at=0, step_interval_ms=250, move_strategy=None) -> Enemy:
    if move_strategy is None:
        move_strategy = lambda maze, enemy, player_pos, rng, blocked: (0, 0)
    return Enemy(
        pos=pos,
        direction=(0, 0),
        next_step_at=next_step_at,
        type=EnemyType.SLIME,
        step_interval_ms=step_interval_ms,
        move_strategy=move_strategy,
    )


def test_update_enemies_does_not_call_strategy_before_timer() -> None:
    maze = [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
    ]
    calls = {"count": 0}

    def strategy(maze, enemy, player_pos, rng, blocked):
        calls["count"] += 1
        return (0, 0)

    enemy = _make_enemy(next_step_at=200, move_strategy=strategy)

    update_enemies(
        enemies=[enemy],
        maze=maze,
        player_pos=(1, 1),
        rng=random.Random(1),
        blocked_set=set(),
        now_ms=100,
    )

    assert calls["count"] == 0
    assert enemy.pos == (1, 1)
    assert enemy.next_step_at == 200


def test_update_enemies_moves_enemy_when_cell_is_open() -> None:
    maze = [
        [1, 1, 1, 1],
        [1, 0, 0, 1],
        [1, 1, 1, 1],
    ]
    enemy = _make_enemy(move_strategy=lambda maze, enemy, player_pos, rng, blocked: (0, 1))

    update_enemies(
        enemies=[enemy],
        maze=maze,
        player_pos=(1, 2),
        rng=random.Random(1),
        blocked_set=set(),
        now_ms=100,
    )

    assert enemy.pos == (1, 2)
    assert enemy.direction == (0, 1)
    assert enemy.last_pos == (1, 1)
    assert enemy.next_step_at == 350


def test_update_enemies_keeps_position_when_move_hits_wall() -> None:
    maze = [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
    ]
    enemy = _make_enemy(move_strategy=lambda maze, enemy, player_pos, rng, blocked: (0, 1))

    update_enemies(
        enemies=[enemy],
        maze=maze,
        player_pos=(1, 1),
        rng=random.Random(1),
        blocked_set=set(),
        now_ms=100,
    )

    assert enemy.pos == (1, 1)
    assert enemy.next_step_at == 350


def test_update_enemies_keeps_position_when_move_hits_blocked_set() -> None:
    maze = [
        [1, 1, 1, 1],
        [1, 0, 0, 1],
        [1, 1, 1, 1],
    ]
    enemy = _make_enemy(move_strategy=lambda maze, enemy, player_pos, rng, blocked: (0, 1))

    update_enemies(
        enemies=[enemy],
        maze=maze,
        player_pos=(1, 2),
        rng=random.Random(1),
        blocked_set={(1, 2)},
        now_ms=100,
    )

    assert enemy.pos == (1, 1)
    assert enemy.next_step_at == 350


def test_update_enemies_keeps_position_on_zero_direction_but_resets_timer() -> None:
    maze = [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
    ]
    enemy = _make_enemy(move_strategy=lambda maze, enemy, player_pos, rng, blocked: (0, 0))

    update_enemies(
        enemies=[enemy],
        maze=maze,
        player_pos=(1, 1),
        rng=random.Random(1),
        blocked_set=set(),
        now_ms=100,
    )

    assert enemy.pos == (1, 1)
    assert enemy.next_step_at == 350


def test_update_enemies_preserves_current_oscillation_contract_when_stepping_back() -> None:
    maze = [
        [1, 1, 1, 1],
        [1, 0, 0, 0],
        [1, 1, 1, 1],
    ]
    enemy = _make_enemy(
        pos=(1, 2),
        move_strategy=lambda maze, enemy, player_pos, rng, blocked: (0, -1),
    )
    enemy.last_pos = (1, 1)
    enemy.oscillation = 2

    update_enemies(
        enemies=[enemy],
        maze=maze,
        player_pos=(1, 3),
        rng=random.Random(1),
        blocked_set=set(),
        now_ms=100,
    )

    assert enemy.pos == (1, 1)
    assert enemy.last_pos == (1, 2)
    assert enemy.direction == (0, -1)
    assert enemy.oscillation == 3
    assert enemy.next_step_at == 350
