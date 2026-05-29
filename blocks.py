"""Temporary blocking walls (spawn and respawn) for Maze Game."""

from __future__ import annotations

import random
from dataclasses import dataclass

Coord = tuple[int, int]


@dataclass
class Block:
    """Временная перегородка (живая стена) в лабиринте."""
    pos: Coord
    expires_at: int  # время (ms), когда блок исчезает/переставляется

def spawn_blocks(
    maze: list[list[int]],
    count: int,
    rng: random.Random,
    forbidden: set[Coord],
) -> list[Block]:
    """
    Создаёт список из count блоков, расставляя их на проходимых клетках (0),
    не задевая множество forbidden.
    """
    rows_count, cols_count = len(maze), len(maze[0])
    free_cells: list[Coord] = [
        (row, col)
        for row in range(rows_count)
        for col in range(cols_count)
        if maze[row][col] == 0 and (row, col) not in forbidden
    ]
    rng.shuffle(free_cells)

    blocks: list[Block] = []
    for position in free_cells:
        if len(blocks) >= count:
            break
        blocks.append(Block(pos=position, expires_at=0))  # время зададим снаружи
    return blocks


def respawn_block(
    block: Block,
    maze: list[list[int]],
    rng: random.Random,
    forbidden: set[Coord],
) -> None:
    """
    Телепортирует block на новую свободную клетку (0), не задевая forbidden.
    Ничего не возвращает — обновляет block.pos.
    """
    rows_count, cols_count = len(maze), len(maze[0])
    candidates: list[Coord] = [
        (row, col)
        for row in range(rows_count)
        for col in range(cols_count)
        if maze[row][col] == 0 and (row, col) not in forbidden
    ]
    if candidates:
        block.pos = rng.choice(candidates)

