from __future__ import annotations

"""SQLite-backed run write path for completed Maze Game runs."""

import datetime as _dt
import os
from typing import TYPE_CHECKING

from db_manager import get_connection


PathType = str | os.PathLike[str]

if TYPE_CHECKING:
    from session_controller import RunResult


def write_completed_run(db_path: PathType, result: "RunResult") -> None:
    """
    Пишет завершённый забег в SQLite и обновляет player_stats.

    Владеет только persistence-ответственностью:
    - INSERT в runs;
    - UPDATE агрегатов в player_stats;
    - win-only policy для best_time_ms;
    - transaction/cursor/connection handling.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        try:
            timestamp_utc = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            cursor.execute(
                """
                INSERT INTO runs (
                    player_id,
                    score,
                    elapsed_ms,
                    coins_value,
                    won,
                    bronze_count,
                    silver_count,
                    gold_count,
                    diamond_count,
                    timestamp_utc
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    result.player_id,
                    result.score,
                    result.elapsed_ms,
                    result.coins_value_sum,
                    1 if result.won else 0,
                    result.bronze_count,
                    result.silver_count,
                    result.gold_count,
                    result.diamond_count,
                    timestamp_utc,
                ),
            )

            cursor.execute(
                """
                UPDATE player_stats
                SET
                    best_score = CASE
                        WHEN ? > best_score THEN ?
                        ELSE best_score
                    END,
                    max_coins = CASE
                        WHEN ? > max_coins THEN ?
                        ELSE max_coins
                    END,
                    best_time_ms = CASE
                        WHEN ? = 1 THEN
                            CASE
                                WHEN best_time_ms IS NULL THEN ?
                                WHEN ? < best_time_ms THEN ?
                                ELSE best_time_ms
                            END
                        ELSE best_time_ms
                    END,
                    total_runs = total_runs + 1,
                    wins = wins + ?,
                    deaths = deaths + ?,
                    total_time_ms = total_time_ms + ?,
                    total_coins = total_coins + ?,
                    bronze_total = bronze_total + ?,
                    silver_total = silver_total + ?,
                    gold_total = gold_total + ?,
                    diamond_total = diamond_total + ?
                WHERE player_id = ?;
                """,
                (
                    result.score,
                    result.score,
                    result.coins_value_sum,
                    result.coins_value_sum,
                    1 if result.won else 0,
                    result.elapsed_ms,
                    result.elapsed_ms,
                    result.elapsed_ms,
                    1 if result.won else 0,
                    0 if result.won else 1,
                    result.elapsed_ms,
                    result.coins_value_sum,
                    result.bronze_count,
                    result.silver_count,
                    result.gold_count,
                    result.diamond_count,
                    result.player_id,
                ),
            )

            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()
