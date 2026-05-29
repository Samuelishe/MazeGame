"""Scoring helpers for completed Maze Game runs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreParams:
    """
    Parameters for final score calculation.

    ``coin_k`` multiplies the total collected coin value.
    ``time_penalty_per_sec`` subtracts points for elapsed time.
    ``win_bonus`` adds a flat bonus on victory.
    ``win_multiplier`` and ``loss_multiplier`` scale the final base score.
    ``diamond_bonus`` adds bonus points per collected diamond on top of the
    regular coin-value contribution.
    ``apply_time_on_loss`` controls whether time penalty also applies on loss.
    """

    coin_k: int = 30
    time_penalty_per_sec: float = 0.25
    win_bonus: int = 400
    win_multiplier: float = 1.25
    loss_multiplier: float = 0.35
    diamond_bonus: int = 400
    apply_time_on_loss: bool = False


def compute_score(
    coins_value_sum: int,
    elapsed_ms: int,
    *,
    won: bool,
    diamond_count: int,
    params: ScoreParams,
) -> int:
    """
    Compute the final score for one completed run.

    Formula:

    ``coin_points = coins_value_sum * coin_k + diamond_count * diamond_bonus``
    ``time_penalty = elapsed_seconds * time_penalty_per_sec``
    ``base = coin_points - time_penalty`` when time penalty applies
    ``base += win_bonus`` on victory
    ``score = base * win_multiplier`` on victory
    ``score = base * loss_multiplier`` on defeat

    The result is rounded to the nearest integer and never goes below zero.

    :param coins_value_sum: Total collected coin value for the run.
    :param elapsed_ms: Run duration in milliseconds.
    :param won: Whether the run ended in victory.
    :param diamond_count: Number of collected diamonds.
    :param params: Scoring parameter set.
    :return: Final non-negative integer score.
    """
    seconds = elapsed_ms / 1000.0
    coin_points = coins_value_sum * params.coin_k + diamond_count * params.diamond_bonus

    if won or params.apply_time_on_loss:
        time_penalty = seconds * params.time_penalty_per_sec
    else:
        time_penalty = 0.0

    base = coin_points - time_penalty

    if won:
        base += params.win_bonus

    multiplier = params.win_multiplier if won else params.loss_multiplier
    final_score = int(round(base * multiplier))
    return max(0, final_score)
