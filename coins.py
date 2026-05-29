"""
coins.py — монеты с редкостями и отрисовкой.

Редкости:
- BRONZE (🥉):  value=1,  weight=0.55
- SILVER (🥈):  value=3,  weight=0.25
- GOLD (🥇):    value=7,  weight=0.17
- DIAMOND (💎): value=20, weight=0.03
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
import random
from typing import Dict, List, Optional, Tuple

import pygame

Coord = Tuple[int, int]


class CoinRarity(Enum):
    """Тип редкости монеты."""
    BRONZE = auto()
    SILVER = auto()
    GOLD = auto()
    DIAMOND = auto()


@dataclass(frozen=True)
class RarityConfig:
    value: int
    rgb: Tuple[int, int, int]
    weight: float


RARITY_CONFIG: Dict[CoinRarity, RarityConfig] = {
    CoinRarity.BRONZE: RarityConfig(value=1, rgb=(205, 127, 50), weight=0.55),
    CoinRarity.SILVER: RarityConfig(value=3, rgb=(192, 192, 192), weight=0.25),
    CoinRarity.GOLD: RarityConfig(value=7, rgb=(255, 215, 0), weight=0.17),
    CoinRarity.DIAMOND: RarityConfig(value=20, rgb=(120, 240, 255), weight=0.03),
}


@dataclass
class Coin:
    """Монета на сетке лабиринта."""
    pos: Coord
    rarity: CoinRarity
    value: int  # дублируем из конфигурации ради удобства подсчётов


def _choose_rarity(rng: random.Random) -> CoinRarity:
    """Выбор редкости по весам из RARITY_CONFIG."""
    items = list(RARITY_CONFIG.items())
    rarities = [r for r, _ in items]
    weights = [cfg.weight for _, cfg in items]
    # random.choices даёт повторения; нам нужен один выбор
    return rng.choices(rarities, weights=weights, k=1)[0]


def spawn_coins(
    maze: List[List[int]],
    count: int,
    rng: random.Random,
    forbidden: set[Coord],
    *,
    ensure_min: Optional[Dict[CoinRarity, int]] = None,
) -> List[Coin]:
    """
    Размещает монеты в свободных ячейках лабиринта, не задевая запрещённые клетки.

    Алгоритм:
    1) собираем список свободных клеток (кроме forbidden) и перемешиваем его;
    2) формируем список редкостей:
       - сначала добавляем гарантированный минимум из ensure_min;
       - оставшиеся слоты добиваем случайными редкостями по весам RARITY_CONFIG;
    3) перемешиваем список редкостей и раскладываем по свободным клеткам.

    :param maze: двумерный список (матрица лабиринта), где 0 — свободная клетка, 1 — стена.
    :param count: целевое количество монет (не больше числа доступных свободных клеток).
    :param rng: экземпляр random.Random для контролируемого выбора позиций и редкостей.
    :param forbidden: множество координат (row, col), где нельзя ставить монеты
                      (например, позиции игрока, врагов или временных блоков).
    :param ensure_min: опциональный словарь {CoinRarity: int}, гарантирующий минимум монет
                       по каждой указанной редкости. Например:
                       {CoinRarity.DIAMOND: 1, CoinRarity.GOLD: 2, ...}.
                       Если доступных клеток мало, часть требований может быть не выполнена.
    :return: список объектов Coin с позицией, редкостью и ценностью.
    """
    rows_count, cols_count = len(maze), len(maze[0])
    free_cells: List[Coord] = [
        (row, col)
        for row in range(rows_count)
        for col in range(cols_count)
        if maze[row][col] == 0 and (row, col) not in forbidden
    ]
    rng.shuffle(free_cells)

    if not free_cells or count <= 0:
        return []

    max_coins = min(count, len(free_cells))

    rarities: List[CoinRarity] = []

    # 1) гарантированный минимум по редкостям
    if ensure_min:
        for rarity, min_amount in ensure_min.items():
            for _ in range(min_amount):
                if len(rarities) >= max_coins:
                    break
                rarities.append(rarity)

    # 2) оставшиеся слоты — случайные по весам
    while len(rarities) < max_coins:
        rarities.append(_choose_rarity(rng))

    rng.shuffle(rarities)

    coins: List[Coin] = []
    for position, rarity in zip(free_cells, rarities):
        value = RARITY_CONFIG[rarity].value
        coins.append(Coin(pos=position, rarity=rarity, value=value))

    return coins


def rarity_icon(rarity: CoinRarity) -> str:
    """Эмодзи для HUD/оверлея по редкости."""
    return {
        CoinRarity.BRONZE: "🥉",
        CoinRarity.SILVER: "🥈",
        CoinRarity.GOLD: "🥇",
        CoinRarity.DIAMOND: "💎",
    }[rarity]

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
    import pygame

    # Подбираем размер относительно клетки
    size = max(6, int(cell_px * 0.55))
    half = size // 2

    table_w = int(size * 0.60)
    table_h = max(2, int(size * 0.22))
    crown_h = max(2, int(size * 0.28))
    pavilion_h = max(3, int(size * 0.58))

    top_y = center_y - (crown_h + table_h // 2)
    girdle_y = center_y + crown_h // 2
    bottom_y = center_y + pavilion_h

    # Контур (силуэт): плоский верх, рундист по бокам, нижний пик
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

    # Фасетки (слегка осветняем базовый цвет)
    light = (min(255, base_rgb[0] + 90), min(255, base_rgb[1] + 90), min(255, base_rgb[2] + 90))
    mid = (min(255, base_rgb[0] + 50), min(255, base_rgb[1] + 50), min(255, base_rgb[2] + 50))

    # Корона: два треугольника от table к рундисту
    left_crown = [(center_x - table_w // 2, top_y), (center_x, top_y), (center_x - half, girdle_y)]
    right_crown = [(center_x, top_y), (center_x + table_w // 2, top_y), (center_x + half, girdle_y)]
    pygame.draw.polygon(screen, light, left_crown)
    pygame.draw.polygon(screen, light, right_crown)

    # Павильон: нижние фасетки
    left_pav = [(center_x - half, girdle_y), (center_x, bottom_y), (center_x - table_w // 2, top_y)]
    right_pav = [(center_x + half, girdle_y), (center_x, bottom_y), (center_x + table_w // 2, top_y)]
    pygame.draw.polygon(screen, mid, left_pav)
    pygame.draw.polygon(screen, mid, right_pav)

    # Table (плоская площадка) — прямоугольник чуть светлее
    table_rect = pygame.Rect(
        center_x - table_w // 2 + 1, top_y + 1, max(1, table_w - 2), table_h
    )
    table_rgb = (min(255, base_rgb[0] + 110), min(255, base_rgb[1] + 110), min(255, base_rgb[2] + 110))
    pygame.draw.rect(screen, table_rgb, table_rect)

    # Блики (тонкие ребра)
    pygame.draw.line(screen, (255, 255, 255), (center_x, top_y), (center_x, bottom_y), width=1)
    pygame.draw.line(
        screen, (255, 255, 255),
        (center_x - table_w // 3, top_y + 2),
        (center_x - half + 2, girdle_y - 1),
        width=1,
    )
    pygame.draw.line(
        screen, (255, 255, 255),
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

    # круглая монета
    base_rgb = cfg.rgb
    pygame.draw.circle(screen, base_rgb, (center_x, center_y), radius)
    pygame.draw.circle(screen, (0, 0, 0), (center_x, center_y), radius, width=1)
    # «блик»
    pygame.draw.circle(
        screen,
        (255, 255, 230),
        (center_x - radius // 3, center_y - radius // 3),
        max(1, radius // 3),
    )
