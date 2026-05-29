from pathlib import Path

from db_manager import get_connection, init_db
from domain.player_models import PlayerProfile
from persistence.player_repository import (
    create_player,
    delete_player,
    get_or_create_player,
    get_player_by_name,
    load_players,
)


def _make_test_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test_maze_stats.db"
    init_db(db_path)
    return db_path


def test_load_players_returns_empty_list_for_fresh_db(tmp_path: Path) -> None:
    db_path = _make_test_db(tmp_path)

    assert load_players(db_path) == []


def test_create_player_returns_profile_with_initialized_stats(tmp_path: Path) -> None:
    db_path = _make_test_db(tmp_path)

    profile = create_player(db_path, "Alice")

    assert isinstance(profile, PlayerProfile)
    assert profile.player_id > 0
    assert profile.name == "Alice"
    assert profile.stats is not None
    assert profile.stats.best_score == 0
    assert profile.stats.best_time_ms is None
    assert profile.stats.total_runs == 0
    assert profile.stats.total_coins == 0


def test_create_player_rejects_duplicate_name(tmp_path: Path) -> None:
    db_path = _make_test_db(tmp_path)
    create_player(db_path, "Alice")

    try:
        create_player(db_path, "Alice")
    except ValueError as exc:
        assert "уже существует" in str(exc)
    else:
        raise AssertionError("Expected ValueError for duplicate player name.")


def test_get_player_by_name_returns_profile_and_none_for_missing(tmp_path: Path) -> None:
    db_path = _make_test_db(tmp_path)
    created = create_player(db_path, "Alice")

    found = get_player_by_name(db_path, "Alice")
    missing = get_player_by_name(db_path, "Bob")

    assert found == created
    assert missing is None


def test_get_or_create_player_returns_existing_player(tmp_path: Path) -> None:
    db_path = _make_test_db(tmp_path)
    created = create_player(db_path, "Alice")

    loaded = get_or_create_player(db_path, "Alice")

    assert loaded == created
    assert load_players(db_path) == [created]


def test_get_or_create_player_creates_player_when_missing(tmp_path: Path) -> None:
    db_path = _make_test_db(tmp_path)

    profile = get_or_create_player(db_path, "Alice")

    assert profile.name == "Alice"
    assert len(load_players(db_path)) == 1
    assert get_player_by_name(db_path, "Alice") == profile


def test_delete_player_removes_player_stats_and_runs(tmp_path: Path) -> None:
    db_path = _make_test_db(tmp_path)
    profile = create_player(db_path, "Alice")

    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        try:
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
                (profile.player_id, 10, 1000, 2, 1, 1, 0, 0, 0, "2026-05-29T00:00:00Z"),
            )
            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()

    delete_player(db_path, profile.player_id)

    assert get_player_by_name(db_path, "Alice") is None
    assert load_players(db_path) == []

    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) AS c FROM player_stats WHERE player_id = ?;", (profile.player_id,))
            stats_count = int(cursor.fetchone()["c"])
            cursor.execute("SELECT COUNT(*) AS c FROM runs WHERE player_id = ?;", (profile.player_id,))
            runs_count = int(cursor.fetchone()["c"])
        finally:
            cursor.close()
    finally:
        connection.close()

    assert stats_count == 0
    assert runs_count == 0
