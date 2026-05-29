"""Pure helpers for translating maze border coordinates into inner cells."""

from __future__ import annotations

Coord = tuple[int, int]


def inner_cell_from_border(border: Coord, side: str) -> Coord:
    """
    Convert a border entry/exit cell into the adjacent inner maze cell.

    Supported sides preserve current Maze Game behavior:

    - ``left`` -> ``(row, col + 1)``
    - ``right`` -> ``(row, col - 1)``
    - ``top`` -> ``(row + 1, col)``
    - ``bottom`` -> ``(row - 1, col)``
    """
    row, col = border
    if side == "left":
        return row, col + 1
    if side == "right":
        return row, col - 1
    if side == "top":
        return row + 1, col
    if side == "bottom":
        return row - 1, col
    raise ValueError(f"Unsupported side: {side!r}")
