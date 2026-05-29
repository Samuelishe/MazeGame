from __future__ import annotations

"""Runtime-facing helper for per-tick enemy movement updates."""

import random

from enemies import Enemy

Coord = tuple[int, int]


def update_enemies(
    *,
    enemies: list[Enemy],
    maze: list[list[int]],
    player_pos: Coord,
    rng: random.Random,
    blocked_set: set[Coord],
    now_ms: int,
) -> None:
    """Updates enemy movement timers and positions in-place."""
    maze_rows = len(maze)
    maze_cols = len(maze[0])

    for enemy in enemies:
        if now_ms < enemy.next_step_at:
            continue

        drow, dcol = enemy.move_strategy(
            maze,
            enemy,
            player_pos,
            rng,
            blocked_set,
        )
        if (drow, dcol) != (0, 0):
            next_row = enemy.pos[0] + drow
            next_col = enemy.pos[1] + dcol

            in_row_bounds = 0 <= next_row < maze_rows
            in_col_bounds = 0 <= next_col < maze_cols
            if in_row_bounds and in_col_bounds:
                is_open_cell = maze[next_row][next_col] == 0
                not_blocked = (next_row, next_col) not in blocked_set
                if is_open_cell and not_blocked:
                    prev_pos = enemy.pos
                    new_pos = (next_row, next_col)

                    if enemy.last_pos is not None and new_pos == enemy.last_pos:
                        enemy.oscillation = min(enemy.oscillation + 1, 10)
                    else:
                        enemy.oscillation = 0

                    enemy.last_pos = prev_pos
                    enemy.pos = new_pos
                    enemy.direction = (drow, dcol)

        enemy.next_step_at = now_ms + enemy.step_interval_ms
