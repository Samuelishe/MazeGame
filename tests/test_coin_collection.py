from __future__ import annotations

from coins import Coin, CoinRarity
from runtime.coin_collection import CoinCollectionStats, collect_coin_at


class _FakeSound:
    def __init__(self) -> None:
        self.coin_calls = 0
        self.diamond_calls = 0

    def play_coin(self) -> None:
        self.coin_calls += 1

    def play_diamond(self) -> None:
        self.diamond_calls += 1


class _FakeEffects:
    def __init__(self) -> None:
        self.flashes: list[tuple[tuple[int, int], int]] = []

    def add_coin_flash(self, cell: tuple[int, int], now_ms: int) -> None:
        self.flashes.append((cell, now_ms))


def test_collect_coin_at_returns_false_when_no_coin_matches() -> None:
    coins = [Coin(pos=(1, 1), rarity=CoinRarity.BRONZE, value=1)]
    stats = CoinCollectionStats()
    sound = _FakeSound()
    effects = _FakeEffects()

    collected = collect_coin_at(
        position=(2, 2),
        current_ms=100,
        coins=coins,
        stats=stats,
        sound=sound,
        effects=effects,
    )

    assert collected is False
    assert coins == [Coin(pos=(1, 1), rarity=CoinRarity.BRONZE, value=1)]
    assert stats == CoinCollectionStats()
    assert sound.coin_calls == 0
    assert sound.diamond_calls == 0
    assert effects.flashes == []


def test_collect_coin_at_updates_regular_coin_stats_and_side_effects() -> None:
    for rarity, value, field_name in (
        (CoinRarity.BRONZE, 1, "bronze_count"),
        (CoinRarity.SILVER, 3, "silver_count"),
        (CoinRarity.GOLD, 7, "gold_count"),
    ):
        coins = [
            Coin(pos=(4, 4), rarity=rarity, value=value),
            Coin(pos=(5, 5), rarity=CoinRarity.DIAMOND, value=20),
        ]
        stats = CoinCollectionStats()
        sound = _FakeSound()
        effects = _FakeEffects()

        collected = collect_coin_at(
            position=(4, 4),
            current_ms=250,
            coins=coins,
            stats=stats,
            sound=sound,
            effects=effects,
        )

        assert collected is True
        assert stats.total_value == value
        assert getattr(stats, field_name) == 1
        assert sound.coin_calls == 1
        assert sound.diamond_calls == 0
        assert effects.flashes == [((4, 4), 250)]
        assert coins == [Coin(pos=(5, 5), rarity=CoinRarity.DIAMOND, value=20)]


def test_collect_coin_at_updates_diamond_stats_and_uses_diamond_sound() -> None:
    coins = [
        Coin(pos=(3, 3), rarity=CoinRarity.BRONZE, value=1),
        Coin(pos=(7, 7), rarity=CoinRarity.DIAMOND, value=20),
    ]
    stats = CoinCollectionStats()
    sound = _FakeSound()
    effects = _FakeEffects()

    collected = collect_coin_at(
        position=(7, 7),
        current_ms=900,
        coins=coins,
        stats=stats,
        sound=sound,
        effects=effects,
    )

    assert collected is True
    assert stats.total_value == 20
    assert stats.diamond_count == 1
    assert sound.coin_calls == 0
    assert sound.diamond_calls == 1
    assert effects.flashes == [((7, 7), 900)]
    assert coins == [Coin(pos=(3, 3), rarity=CoinRarity.BRONZE, value=1)]


def test_collect_coin_at_collects_only_matching_position() -> None:
    coins = [
        Coin(pos=(1, 1), rarity=CoinRarity.BRONZE, value=1),
        Coin(pos=(2, 2), rarity=CoinRarity.SILVER, value=3),
        Coin(pos=(3, 3), rarity=CoinRarity.GOLD, value=7),
    ]
    stats = CoinCollectionStats()
    sound = _FakeSound()
    effects = _FakeEffects()

    collected = collect_coin_at(
        position=(2, 2),
        current_ms=444,
        coins=coins,
        stats=stats,
        sound=sound,
        effects=effects,
    )

    assert collected is True
    assert stats.total_value == 3
    assert stats.silver_count == 1
    assert len(coins) == 2
    assert Coin(pos=(1, 1), rarity=CoinRarity.BRONZE, value=1) in coins
    assert Coin(pos=(3, 3), rarity=CoinRarity.GOLD, value=7) in coins
    assert effects.flashes == [((2, 2), 444)]
