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
