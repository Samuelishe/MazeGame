"""Визуальные эффекты Maze Game (без тяжелых анимаций).

Содержит вспышку на клетке после сбора монеты.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, List

import pygame

Coord = Tuple[int, int]


@dataclass
class CoinFlash:
    """Короткая вспышка на клетке после сбора монеты."""
    cell: Coord
    start_ms: int
    duration_ms: int = 220  # ~0.22s

    def alive(self, now_ms: int) -> bool:
        return now_ms - self.start_ms < self.duration_ms

    def alpha(self, now_ms: int) -> int:
        t = (now_ms - self.start_ms) / self.duration_ms
        t = max(0.0, min(1.0, t))
        return int(180 * (1.0 - t))  # затухание


class Effects:
    """Хранилище и отрисовка простых эффектов."""

    def __init__(self) -> None:
        self._flashes: List[CoinFlash] = []

    def reset(self) -> None:
        """Очищает все активные эффекты."""
        self._flashes.clear()

    def add_coin_flash(self, cell: Coord, now_ms: int) -> None:
        """Добавить вспышку на клетке."""
        self._flashes.append(CoinFlash(cell=cell, start_ms=now_ms))

    def draw_all(self, screen: "pygame.Surface", cell_px: int, now_ms: int) -> None:
        """Отрисовать и подчистить эффекты."""
        alive: List[CoinFlash] = []
        for fx in self._flashes:
            if not fx.alive(now_ms):
                continue
            alive.append(fx)

            row, col = fx.cell
            x = col * cell_px
            y = row * cell_px

            # полупрозрачная «аура» + белое свечение в центре
            aura = pygame.Surface((cell_px, cell_px), pygame.SRCALPHA)
            aura.fill((255, 255, 255, fx.alpha(now_ms)))
            screen.blit(aura, (x, y))

            inner = pygame.Surface((int(cell_px * 0.6), int(cell_px * 0.6)), pygame.SRCALPHA)
            inner.fill((255, 255, 255, min(200, fx.alpha(now_ms) + 40)))
            screen.blit(
                inner,
                (int(x + cell_px * 0.2), int(y + cell_px * 0.2)),
            )

        self._flashes = alive
