"""Color palette generation for Maze Game."""

from __future__ import annotations

import colorsys
import random
from typing import Optional


def make_palette(seed: Optional[int] = None) -> dict[str, tuple[int, int, int]]:
    """
    Генерирует согласованную палитру RGB (стены/путь/игрок/цель) из одного hue.
    """
    rng = random.Random(seed)
    hue = rng.random()
    wall = colorsys.hsv_to_rgb(hue, 0.35, 0.98)
    path = colorsys.hsv_to_rgb(hue, 0.65, 0.30)
    wall_rgb = tuple(int(x * 255) for x in wall)
    path_rgb = tuple(int(x * 255) for x in path)
    player_rgb = (255, 220, 90)
    goal_rgb = (90, 220, 255)
    return {"wall": wall_rgb, "path": path_rgb, "player": player_rgb, "goal": goal_rgb}
