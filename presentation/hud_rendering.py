"""HUD surface composition helpers."""

from __future__ import annotations

import pygame


def compose_hud_background(
    hud_surf: "pygame.Surface",
    *,
    pad_x: int = 6,
    pad_y: int = 4,
    bg_rgba: tuple[int, int, int, int] = (0, 0, 0, 135),
    border_radius: int = 6,
) -> tuple["pygame.Surface", int, int]:
    """
    Собирает полупрозрачную HUD-подложку под уже готовую поверхность текста.

    Возвращает:
      - готовую background surface;
      - pad_x;
      - pad_y.

    Паддинги возвращаются явно, чтобы вызывающий код мог сохранить прежнюю
    политику позиционирования текста без скрытых констант.
    """
    hud_width = hud_surf.get_width() + pad_x * 2
    hud_height = hud_surf.get_height() + pad_y * 2

    hud_bg = pygame.Surface((hud_width, hud_height), pygame.SRCALPHA)
    hud_bg.fill(bg_rgba)
    pygame.draw.rect(
        hud_bg,
        bg_rgba,
        (0, 0, hud_width, hud_height),
        border_radius=border_radius,
    )
    return hud_bg, pad_x, pad_y
