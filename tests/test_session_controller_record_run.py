from pathlib import Path

from db_manager import get_connection, init_db
from session_controller import GameSessionController, RunResult


def _make_test_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test_record_run.db"
    init_db(db_path)
    return db_path


def _make_session(tmp_path: Path) -> tuple[Path, GameSessionController, int]:
    db_path = _make_test_db(tmp_path)
    session = GameSessionController.from_db(db_path)
    player_id = session.current_player().player_id
    return db_path, session, player_id


def _make_result(
    player_id: int,
    *,
    score: int = 100,
    elapsed_ms: int = 10_000,
    coins_value_sum: int = 5,
    won: bool = True,
    bronze_count: int = 1,
    silver_count: int = 0,
    gold_count: int = 0,
    diamond_count: int = 0,
) -> RunResult:
    return RunResult(
        player_id=player_id,
        score=score,
        elapsed_ms=elapsed_ms,
        coins_value_sum=coins_value_sum,
        won=won,
        bronze_count=bronze_count,
        silver_count=silver_count,
        gold_count=gold_count,
        diamond_count=diamond_count,
    )


def _fetch_runs_for_player(db_path: Path, player_id: int) -> list[dict[str, object]]:
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT
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
                FROM runs
                WHERE player_id = ?
                ORDER BY run_id ASC;
                """,
                (player_id,),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
    finally:
        connection.close()

    return [dict(row) for row in rows]


def _fetch_player_stats(db_path: Path, player_id: int) -> dict[str, object]:
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    best_score,
                    best_time_ms,
                    max_coins,
                    total_runs,
                    wins,
                    deaths,
                    total_time_ms,
                    total_coins,
                    bronze_total,
                    silver_total,
                    gold_total,
                    diamond_total
                FROM player_stats
                WHERE player_id = ?;
                """,
                (player_id,),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()
    finally:
        connection.close()

    if row is None:
        raise AssertionError(f"Expected player_stats row for player_id={player_id}.")

    return dict(row)


def test_record_run_persists_winning_run_and_updates_session_stats(tmp_path: Path) -> None:
    db_path, session, player_id = _make_session(tmp_path)

    result = _make_result(
        player_id,
        score=420,
        elapsed_ms=8_765,
        coins_value_sum=17,
        won=True,
        bronze_count=2,
        silver_count=3,
        gold_count=1,
        diamond_count=1,
    )

    session.record_run(result)

    runs = _fetch_runs_for_player(db_path, player_id)
    stats_row = _fetch_player_stats(db_path, player_id)
    session_stats = session.get_session_stats_for(player_id)

    assert len(runs) == 1
    assert runs[0]["player_id"] == player_id
    assert runs[0]["score"] == 420
    assert runs[0]["elapsed_ms"] == 8_765
    assert runs[0]["coins_value"] == 17
    assert runs[0]["won"] == 1
    assert runs[0]["bronze_count"] == 2
    assert runs[0]["silver_count"] == 3
    assert runs[0]["gold_count"] == 1
    assert runs[0]["diamond_count"] == 1
    assert isinstance(runs[0]["timestamp_utc"], str)
    assert runs[0]["timestamp_utc"]

    assert stats_row == {
        "best_score": 420,
        "best_time_ms": 8_765,
        "max_coins": 17,
        "total_runs": 1,
        "wins": 1,
        "deaths": 0,
        "total_time_ms": 8_765,
        "total_coins": 17,
        "bronze_total": 2,
        "silver_total": 3,
        "gold_total": 1,
        "diamond_total": 1,
    }

    assert session_stats.runs == 1
    assert session_stats.wins == 1
    assert session_stats.deaths == 0
    assert session_stats.total_score == 420
    assert session_stats.total_time_ms == 8_765
    assert session_stats.total_coins == 17
    assert session_stats.bronze_total == 2
    assert session_stats.silver_total == 3
    assert session_stats.gold_total == 1
    assert session_stats.diamond_total == 1


def test_record_run_persists_losing_run_without_setting_best_time(tmp_path: Path) -> None:
    db_path, session, player_id = _make_session(tmp_path)

    result = _make_result(
        player_id,
        score=90,
        elapsed_ms=12_345,
        coins_value_sum=6,
        won=False,
        bronze_count=1,
        silver_count=1,
        gold_count=0,
        diamond_count=0,
    )

    session.record_run(result)

    runs = _fetch_runs_for_player(db_path, player_id)
    stats_row = _fetch_player_stats(db_path, player_id)
    session_stats = session.get_session_stats_for(player_id)

    assert len(runs) == 1
    assert runs[0]["won"] == 0

    assert stats_row["total_runs"] == 1
    assert stats_row["wins"] == 0
    assert stats_row["deaths"] == 1
    assert stats_row["best_score"] == 90
    assert stats_row["max_coins"] == 6
    assert stats_row["best_time_ms"] is None
    assert stats_row["total_time_ms"] == 12_345
    assert stats_row["total_coins"] == 6
    assert stats_row["bronze_total"] == 1
    assert stats_row["silver_total"] == 1
    assert stats_row["gold_total"] == 0
    assert stats_row["diamond_total"] == 0

    assert session_stats.runs == 1
    assert session_stats.wins == 0
    assert session_stats.deaths == 1
    assert session_stats.total_score == 90
    assert session_stats.total_time_ms == 12_345
    assert session_stats.total_coins == 6


def test_record_run_keeps_smallest_best_time_across_multiple_wins(tmp_path: Path) -> None:
    db_path, session, player_id = _make_session(tmp_path)

    session.record_run(_make_result(player_id, score=100, elapsed_ms=9_000, won=True))
    session.record_run(_make_result(player_id, score=150, elapsed_ms=7_000, won=True))
    session.record_run(_make_result(player_id, score=180, elapsed_ms=11_000, won=True))

    stats_row = _fetch_player_stats(db_path, player_id)
    runs = _fetch_runs_for_player(db_path, player_id)

    assert len(runs) == 3
    assert stats_row["best_time_ms"] == 7_000
    assert stats_row["wins"] == 3
    assert stats_row["deaths"] == 0
    assert stats_row["total_runs"] == 3


def test_record_run_accumulates_db_and_session_counters_across_runs(tmp_path: Path) -> None:
    db_path, session, player_id = _make_session(tmp_path)

    results = [
        _make_result(
            player_id,
            score=120,
            elapsed_ms=5_000,
            coins_value_sum=7,
            won=True,
            bronze_count=1,
            silver_count=0,
            gold_count=1,
            diamond_count=0,
        ),
        _make_result(
            player_id,
            score=80,
            elapsed_ms=7_500,
            coins_value_sum=3,
            won=False,
            bronze_count=0,
            silver_count=1,
            gold_count=0,
            diamond_count=0,
        ),
        _make_result(
            player_id,
            score=200,
            elapsed_ms=4_500,
            coins_value_sum=12,
            won=True,
            bronze_count=2,
            silver_count=1,
            gold_count=0,
            diamond_count=1,
        ),
    ]

    for result in results:
        session.record_run(result)

    stats_row = _fetch_player_stats(db_path, player_id)
    session_stats = session.get_session_stats_for(player_id)

    assert stats_row["total_runs"] == 3
    assert stats_row["wins"] == 2
    assert stats_row["deaths"] == 1
    assert stats_row["best_score"] == 200
    assert stats_row["best_time_ms"] == 4_500
    assert stats_row["max_coins"] == 12
    assert stats_row["total_time_ms"] == 17_000
    assert stats_row["total_coins"] == 22
    assert stats_row["bronze_total"] == 3
    assert stats_row["silver_total"] == 2
    assert stats_row["gold_total"] == 1
    assert stats_row["diamond_total"] == 1

    assert session_stats.runs == 3
    assert session_stats.wins == 2
    assert session_stats.deaths == 1
    assert session_stats.total_score == 400
    assert session_stats.total_time_ms == 17_000
    assert session_stats.total_coins == 22
    assert session_stats.bronze_total == 3
    assert session_stats.silver_total == 2
    assert session_stats.gold_total == 1
    assert session_stats.diamond_total == 1
