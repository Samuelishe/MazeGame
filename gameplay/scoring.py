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


@dataclass(frozen=True)
class PreparedRunScore:
    """
    Prepared score-related values for one completed run.

    This container keeps the data-only preparation step separate from the
    actual score calculation call in runtime code.
    """

    elapsed_ms: int
    coins_value_sum: int
    diamond_count: int
    won: bool
    params: ScoreParams


def prepare_run_score(
    *,
    start_ms: int,
    now_ms: int,
    coins_value_sum: int,
    diamond_count: int,
    won: bool,
) -> PreparedRunScore:
    """
    Prepare pure score-related values for one completed run.

    This helper intentionally does not call ``compute_score``. It only
    prepares:

    - elapsed time derived from ``start_ms`` and ``now_ms``;
    - the current ``ScoreParams`` configuration;
    - the explicit score input values used by runtime code.
    """
    elapsed_ms = now_ms - start_ms
    params = ScoreParams(
        coin_k=30,
        time_penalty_per_sec=0.25,
        win_bonus=400,
        win_multiplier=1.25,
        loss_multiplier=0.35,
        diamond_bonus=400,
        apply_time_on_loss=False,
    )
    return PreparedRunScore(
        elapsed_ms=elapsed_ms,
        coins_value_sum=coins_value_sum,
        diamond_count=diamond_count,
        won=won,
        params=params,
    )


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
