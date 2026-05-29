from __future__ import annotations

"""Runtime-facing helper for end-of-run persistence handoff."""

from typing import TYPE_CHECKING

from highscores import Highscore, save_highscore, update_highscore_if_better
from session_controller import RunResult

if TYPE_CHECKING:
    from session_controller import GameSessionController
    from runtime.session_stats import SessionStats


def handle_run_persistence(
    *,
    highscore: Highscore,
    highscore_json_path: str,
    stats: "SessionStats",
    session_controller: "GameSessionController | None",
    active_player_id: int | None,
    score: int,
    elapsed_ms: int,
    coins_value_sum: int,
    won: bool,
    bronze_count: int,
    silver_count: int,
    gold_count: int,
    diamond_count: int,
) -> None:
    """
    Выполняет end-of-run persistence handoff без UI и без расчёта значений.

    Владеет только orchestration-уровнем:
    - обновляет legacy highscore JSON через existing highscores helpers;
    - при отсутствии session_controller обновляет standalone SessionStats;
    - при наличии session_controller создаёт RunResult и делегирует запись контроллеру.
    """
    if update_highscore_if_better(
        highscore,
        score=score,
        coins_value_sum=coins_value_sum,
        elapsed_ms=elapsed_ms,
        won=won,
        bronze_count=bronze_count,
        silver_count=silver_count,
        gold_count=gold_count,
        diamond_count=diamond_count,
    ):
        save_highscore(highscore, highscore_json_path)

    if session_controller is None or active_player_id is None:
        stats.add_result(
            won=won,
            coins_value_sum=coins_value_sum,
            elapsed_ms=elapsed_ms,
            score=score,
            bronze_count=bronze_count,
            silver_count=silver_count,
            gold_count=gold_count,
            diamond_count=diamond_count,
        )
        return

    run_result = RunResult(
        player_id=active_player_id,
        score=score,
        elapsed_ms=elapsed_ms,
        coins_value_sum=coins_value_sum,
        won=won,
        bronze_count=bronze_count,
        silver_count=silver_count,
        gold_count=gold_count,
        diamond_count=diamond_count,
    )
    session_controller.record_run(run_result)
