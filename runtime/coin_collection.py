from __future__ import annotations

"""Runtime-facing helper for coin pickup accounting and side effects."""

from dataclasses import dataclass
from typing import Protocol, TYPE_CHECKING

from coins import Coin, CoinRarity

if TYPE_CHECKING:
    from effects import Effects
    from sounds import SoundBank

Coord = tuple[int, int]


class _CoinSoundLike(Protocol):
    def play_coin(self) -> None: ...

    def play_diamond(self) -> None: ...


class _CoinEffectsLike(Protocol):
    def add_coin_flash(self, cell: Coord, now_ms: int) -> None: ...


@dataclass
class CoinCollectionStats:
    total_value: int = 0
    bronze_count: int = 0
    silver_count: int = 0
    gold_count: int = 0
    diamond_count: int = 0


def collect_coin_at(
    *,
    position: Coord,
    current_ms: int,
    coins: list[Coin],
    stats: CoinCollectionStats,
    sound: _CoinSoundLike,
    effects: _CoinEffectsLike,
) -> bool:
    """
    Ищет монету в заданной клетке, применяет side effects и обновляет счётчики.

    Возвращает True, если монета была собрана, иначе False.
    """
    for coin_ in coins[:]:
        if coin_.pos != position:
            continue

        stats.total_value += coin_.value
        if coin_.rarity is CoinRarity.BRONZE:
            stats.bronze_count += 1
            sound.play_coin()
        elif coin_.rarity is CoinRarity.SILVER:
            stats.silver_count += 1
            sound.play_coin()
        elif coin_.rarity is CoinRarity.GOLD:
            stats.gold_count += 1
            sound.play_coin()
        else:
            stats.diamond_count += 1
            sound.play_diamond()

        effects.add_coin_flash(position, current_ms)
        coins.remove(coin_)
        return True

    return False
