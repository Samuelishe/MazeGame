"""Temporary block rendering helpers extracted from mixed gameplay support code."""

from __future__ import annotations

import math

import pygame


def _pulse_color(base_rgb: tuple[int, int, int], now_ms: int, period_ms: int) -> tuple[int, int, int]:
    """
    Меняет яркость по синусу в диапазоне [0.6..1.0] от исходного цвета.
    """
    phase = (now_ms % period_ms) / period_ms
    k = 0.6 + 0.4 * math.sin(2 * math.pi * phase)
    r = max(0, min(255, int(base_rgb[0] * k)))
    g = max(0, min(255, int(base_rgb[1] * k)))
    b = max(0, min(255, int(base_rgb[2] * k)))
    return r, g, b


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
