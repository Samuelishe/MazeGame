"""Temporary blocking walls (spawn, respawn, draw) for Maze Game."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

Coord = tuple[int, int]


@dataclass
class Block:
    """Временная перегородка (живая стена) в лабиринте."""
    pos: Coord
    expires_at: int  # время (ms), когда блок исчезает/переставляется


def _pulse_color(base_rgb: tuple[int, int, int], now_ms: int, period_ms: int) -> tuple[int, int, int]:
    """
    Меняет яркость по синусу в диапазоне [0.6..1.0] от исходного цвета.
    """
    phase = (now_ms % period_ms) / period_ms  # 0..1
    k = 0.6 + 0.4 * math.sin(2 * math.pi * phase)
    r = max(0, min(255, int(base_rgb[0] * k)))
    g = max(0, min(255, int(base_rgb[1] * k)))
    b = max(0, min(255, int(base_rgb[2] * k)))
    return r, g, b


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


def draw_block_cell(
    screen: "pygame.Surface",
    x_px: int,
    y_px: int,
    cell_size_px: int,
    wall_rgb: tuple[int, int, int],
    now_ms: int,
    pulse_ms: int,
) -> None:
    """
    Рисует блок как временную стену:
    - пульсирующий прямоугольник,
    - тонкая чёрная обводка,
    - горизонтальная штриховка внутри.
    """
    block_rgb = _pulse_color(wall_rgb, now_ms, pulse_ms)

    pygame.draw.rect(
        screen, block_rgb, (x_px, y_px, cell_size_px, cell_size_px), border_radius=0
    )
    pygame.draw.rect(
        screen, (0, 0, 0), (x_px, y_px, cell_size_px, cell_size_px), width=1, border_radius=0
    )

    inner_padding_px = max(2, cell_size_px // 10)
    y_start_px = y_px + inner_padding_px
    y_end_px = y_px + cell_size_px - inner_padding_px
    stripe_step_px = max(3, cell_size_px // 6)
    stripe_rgb = (
        max(0, block_rgb[0] - 40),
        max(0, block_rgb[1] - 40),
        max(0, block_rgb[2] - 40),
    )
    for y_line_px in range(y_start_px, y_end_px, stripe_step_px):
        pygame.draw.line(
            screen,
            stripe_rgb,
            (x_px + inner_padding_px, y_line_px),
            (x_px + cell_size_px - inner_padding_px, y_line_px),
            width=1,
        )
