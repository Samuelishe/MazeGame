"""Pure text builders for gameplay HUD output."""

from __future__ import annotations

from gameplay.formatting import format_time


def build_player_prefix(active_player_name: str | None) -> str:
    """
    Build the optional player-name prefix for the HUD line.

    :param active_player_name: Active player name or ``None`` when no player label
        should be shown.
    :return: Prefix with trailing spacing preserved exactly as used by the
        existing HUD layout.
    """
    if active_player_name is None:
        return ""
    return f"Игрок: {active_player_name}   "


def _build_coin_summary(
    *,
    bronze_count: int,
    silver_count: int,
    gold_count: int,
    diamond_count: int,
) -> str:
    """Build the compact per-rarity coin summary used inside the HUD line."""
    return f"(🥉{bronze_count}/🥈{silver_count}/🥇{gold_count}/💎{diamond_count})"


def build_hud_text(
    *,
    active_player_name: str | None,
    coins_collected: int,
    bronze_count: int,
    silver_count: int,
    gold_count: int,
    diamond_count: int,
    elapsed_ms_live: int,
) -> str:
    """
    Build the full single-line HUD text for active gameplay.

    This helper preserves the historical Maze Game text layout and spacing.

    :param active_player_name: Active player name or ``None``.
    :param coins_collected: Total collected coin value.
    :param bronze_count: Bronze coin count.
    :param silver_count: Silver coin count.
    :param gold_count: Gold coin count.
    :param diamond_count: Diamond count.
    :param elapsed_ms_live: Current elapsed time in milliseconds.
    :return: Full HUD text string.
    """
    prefix = build_player_prefix(active_player_name)
    coin_summary = _build_coin_summary(
        bronze_count=bronze_count,
        silver_count=silver_count,
        gold_count=gold_count,
        diamond_count=diamond_count,
    )

    return (
        f"{prefix}"
        f"💰 {coins_collected} "
        f"{coin_summary}   "
        f"⏱ {format_time(elapsed_ms_live)}"
    )
