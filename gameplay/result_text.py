"""Pure text builders for gameplay result summaries."""

from __future__ import annotations

from dataclasses import dataclass

from coins import CoinRarity, rarity_icon
from gameplay.formatting import format_time


@dataclass(frozen=True)
class PreparedEndMenuSummary:
    """
    Deterministic end-screen summary values prepared from runtime data.

    This keeps value preparation separate from pygame overlay flow and
    persistence hooks in ``maze_game.py``.
    """

    best_time_str: str
    high_line: str
    types_line: str
    subtitle: str


def build_attempt_info(
    *,
    won: bool,
    time_str: str,
    coins_value_sum: int,
    score: int,
) -> str:
    """
    Build the first end-screen summary line for one run.

    The output preserves the existing Maze Game wording for victory and defeat.

    :param won: Whether the run ended in victory.
    :param time_str: Preformatted elapsed time string.
    :param coins_value_sum: Total collected coin value.
    :param score: Final score for the run.
    :return: Human-readable attempt summary line.
    """
    if won:
        return f"Время: {time_str} • ценность монет {coins_value_sum} • Очки: {score}"
    return f"Ты держался {time_str} • ценность монет {coins_value_sum} • Очки: {score}"


def build_coin_types_line(
    *,
    bronze_count: int,
    silver_count: int,
    gold_count: int,
    diamond_count: int,
) -> str:
    """
    Build the end-screen line with per-rarity coin counts.

    :param bronze_count: Number of collected bronze coins.
    :param silver_count: Number of collected silver coins.
    :param gold_count: Number of collected gold coins.
    :param diamond_count: Number of collected diamonds.
    :return: Human-readable coin-breakdown line.
    """
    return (
        f"{rarity_icon(CoinRarity.BRONZE)}{bronze_count} • "
        f"{rarity_icon(CoinRarity.SILVER)}{silver_count} • "
        f"{rarity_icon(CoinRarity.GOLD)}{gold_count} • "
        f"{rarity_icon(CoinRarity.DIAMOND)}{diamond_count}"
    )


def build_highscore_line(
    *,
    best_score: int,
    best_time_str: str,
    max_coins_value: int,
    bronze_max: int,
    silver_max: int,
    gold_max: int,
    diamond_max: int,
) -> str:
    """
    Build the end-screen line with legacy highscore summary values.

    :param best_score: Best recorded score.
    :param best_time_str: Preformatted best-time string or placeholder.
    :param max_coins_value: Best recorded total coin value.
    :param bronze_max: Best bronze coin count.
    :param silver_max: Best silver coin count.
    :param gold_max: Best gold coin count.
    :param diamond_max: Best diamond count.
    :return: Human-readable highscore summary line.
    """
    return (
        f"Рекорд: очки {best_score} • время {best_time_str} • "
        f"ценность монет {max_coins_value}  "
        f"🥉{bronze_max} • 🥈{silver_max} • "
        f"🥇{gold_max} • 💎{diamond_max}"
    )


def build_end_menu_subtitle(
    *,
    attempt_info: str,
    types_line: str,
    high_line: str,
    session_info: str,
) -> str:
    """
    Build the full multiline subtitle for the gameplay end menu.

    :param attempt_info: Summary line for the current run.
    :param types_line: Coin-rarity breakdown line.
    :param high_line: Highscore summary line.
    :param session_info: Session summary line.
    :return: Multiline subtitle for the end-screen overlay.
    """
    return (
        f"{attempt_info}\n"
        f"{types_line}\n"
        f"{high_line}\n"
        f"{session_info}\n"
        f"Enter/Space/R — заново • N — другой уровень • Esc — выход"
    )


def prepare_end_menu_summary(
    *,
    attempt_info: str,
    session_info: str,
    best_time_ms: int | None,
    best_score: int,
    max_coins_value: int,
    bronze_max: int,
    silver_max: int,
    gold_max: int,
    diamond_max: int,
    bronze_count: int,
    silver_count: int,
    gold_count: int,
    diamond_count: int,
) -> PreparedEndMenuSummary:
    """
    Prepare deterministic highscore and summary values for the end screen.

    This helper intentionally does not interact with pygame or persistence.
    It only prepares the values and strings that are later passed into the
    existing end-screen overlay flow.
    """
    if best_time_ms is not None:
        best_time_str = format_time(best_time_ms)
    else:
        best_time_str = "—"

    high_line = build_highscore_line(
        best_score=best_score,
        best_time_str=best_time_str,
        max_coins_value=max_coins_value,
        bronze_max=bronze_max,
        silver_max=silver_max,
        gold_max=gold_max,
        diamond_max=diamond_max,
    )
    types_line = build_coin_types_line(
        bronze_count=bronze_count,
        silver_count=silver_count,
        gold_count=gold_count,
        diamond_count=diamond_count,
    )
    subtitle = build_end_menu_subtitle(
        attempt_info=attempt_info,
        types_line=types_line,
        high_line=high_line,
        session_info=session_info,
    )
    return PreparedEndMenuSummary(
        best_time_str=best_time_str,
        high_line=high_line,
        types_line=types_line,
        subtitle=subtitle,
    )
