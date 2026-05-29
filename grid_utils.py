"""Grid utils for Maze Game: directions and bounds checks."""

from __future__ import annotations

from typing import Final


# Четыре ортогональных направления (row, col)
DIRS4: Final[list[tuple[int, int]]] = [
    (-1, 0),  # up
    (1, 0),   # down
    (0, -1),  # left
    (0, 1),   # right
]


def in_bounds(row: int, col: int, rows_count: int, cols_count: int) -> bool:
    """Проверяет, что (row, col) лежит внутри границ сетки."""
    return 0 <= row < rows_count and 0 <= col < cols_count