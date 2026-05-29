"""Coin rendering helpers extracted from mixed gameplay support code."""

from __future__ import annotations

import pygame

from coins import Coin, CoinRarity, RARITY_CONFIG


def _draw_diamond(
    screen: "pygame.Surface",
    center_x: int,
    center_y: int,
    cell_px: int,
    base_rgb: tuple[int, int, int],
) -> None:
    """
    Рисует огранённый алмаз, читабельный на маленьких размерах (cell_px ~16–32).
    Геометрия: table (плоский верх), crown (корона), girdle (рундист), pavilion (павильон).
    """
    size = max(6, int(cell_px * 0.55))
    half = size // 2

    table_w = int(size * 0.60)
    table_h = max(2, int(size * 0.22))
    crown_h = max(2, int(size * 0.28))
    pavilion_h = max(3, int(size * 0.58))

    top_y = center_y - (crown_h + table_h // 2)
    girdle_y = center_y + crown_h // 2
    bottom_y = center_y + pavilion_h

    outline = [
        (center_x - table_w // 2, top_y),
        (center_x + table_w // 2, top_y),
        (center_x + half, girdle_y),
        (center_x, bottom_y),
        (center_x - half, girdle_y),
        (center_x - table_w // 2, top_y),
    ]

    pygame.draw.polygon(screen, base_rgb, outline)
    pygame.draw.lines(screen, (0, 0, 0), False, outline, width=1)

    light = (
        min(255, base_rgb[0] + 90),
        min(255, base_rgb[1] + 90),
        min(255, base_rgb[2] + 90),
    )
    mid = (
        min(255, base_rgb[0] + 50),
        min(255, base_rgb[1] + 50),
        min(255, base_rgb[2] + 50),
    )

    left_crown = [(center_x - table_w // 2, top_y), (center_x, top_y), (center_x - half, girdle_y)]
    right_crown = [(center_x, top_y), (center_x + table_w // 2, top_y), (center_x + half, girdle_y)]
    pygame.draw.polygon(screen, light, left_crown)
    pygame.draw.polygon(screen, light, right_crown)

    left_pav = [(center_x - half, girdle_y), (center_x, bottom_y), (center_x - table_w // 2, top_y)]
    right_pav = [(center_x + half, girdle_y), (center_x, bottom_y), (center_x + table_w // 2, top_y)]
    pygame.draw.polygon(screen, mid, left_pav)
    pygame.draw.polygon(screen, mid, right_pav)

    table_rect = pygame.Rect(
        center_x - table_w // 2 + 1, top_y + 1, max(1, table_w - 2), table_h
    )
    table_rgb = (
        min(255, base_rgb[0] + 110),
        min(255, base_rgb[1] + 110),
        min(255, base_rgb[2] + 110),
    )
    pygame.draw.rect(screen, table_rgb, table_rect)

    pygame.draw.line(screen, (255, 255, 255), (center_x, top_y), (center_x, bottom_y), width=1)
    pygame.draw.line(
        screen,
        (255, 255, 255),
        (center_x - table_w // 3, top_y + 2),
        (center_x - half + 2, girdle_y - 1),
        width=1,
    )
    pygame.draw.line(
        screen,
        (255, 255, 255),
        (center_x + table_w // 3, top_y + 2),
        (center_x + half - 2, girdle_y - 1),
        width=1,
    )


def draw_coin(screen: "pygame.Surface", coin: Coin, cell_px: int) -> None:
    """
    Рисует монету по её редкости:
    - бронза/серебро/золото: круг с бликом,
    - бриллиант: «ромб» (4-угольник) с обводкой.
    """
    row, col = coin.pos
    center_x = col * cell_px + cell_px // 2
    center_y = row * cell_px + cell_px // 2
    radius = max(3, cell_px // 4)

    cfg = RARITY_CONFIG[coin.rarity]

    if coin.rarity is CoinRarity.DIAMOND:
        _draw_diamond(screen, center_x, center_y, cell_px, cfg.rgb)
        return

    base_rgb = cfg.rgb
    pygame.draw.circle(screen, base_rgb, (center_x, center_y), radius)
    pygame.draw.circle(screen, (0, 0, 0), (center_x, center_y), radius, width=1)
    pygame.draw.circle(
        screen,
        (255, 255, 230),
        (center_x - radius // 3, center_y - radius // 3),
        max(1, radius // 3),
    )
