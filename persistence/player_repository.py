from __future__ import annotations

"""SQLite-backed player repository API for Maze Game."""

import os
import sqlite3
from typing import Optional

from db_manager import get_connection
from domain.player_models import PlayerAggregateStats, PlayerProfile


PathType = str | os.PathLike[str]


def _row_to_aggregate_stats(row: sqlite3.Row | None) -> Optional[PlayerAggregateStats]:
    """
    Преобразует строку из player_stats в PlayerAggregateStats.

    :param row: результат SELECT * FROM player_stats ... или None.
    :return: PlayerAggregateStats или None.
    """
    if row is None:
        return None

    return PlayerAggregateStats(
        best_score=int(row["best_score"]),
        best_time_ms=(int(row["best_time_ms"]) if row["best_time_ms"] is not None else None),
        max_coins=int(row["max_coins"]),
        total_runs=int(row["total_runs"]),
        wins=int(row["wins"]),
        deaths=int(row["deaths"]),
        total_time_ms=int(row["total_time_ms"]),
        total_coins=int(row["total_coins"]),
        bronze_total=int(row["bronze_total"]),
        silver_total=int(row["silver_total"]),
        gold_total=int(row["gold_total"]),
        diamond_total=int(row["diamond_total"]),
    )


def load_players(db_path: PathType) -> list[PlayerProfile]:
    """
    Загружает всех игроков из БД вместе с их агрегированной статистикой.

    Игроки сортируются по player_id в порядке создания.

    :param db_path: путь к SQLite-файлу.
    :return: список PlayerProfile.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    p.player_id,
                    p.name,
                    s.best_score,
                    s.best_time_ms,
                    s.max_coins,
                    s.total_runs,
                    s.wins,
                    s.deaths,
                    s.total_time_ms,
                    s.total_coins,
                    s.bronze_total,
                    s.silver_total,
                    s.gold_total,
                    s.diamond_total
                FROM players AS p
                LEFT JOIN player_stats AS s
                    ON s.player_id = p.player_id
                ORDER BY p.player_id ASC;
                """
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
    finally:
        connection.close()

    players: list[PlayerProfile] = []
    for row in rows:
        stats_row = {
            "best_score": row["best_score"],
            "best_time_ms": row["best_time_ms"],
            "max_coins": row["max_coins"],
            "total_runs": row["total_runs"],
            "wins": row["wins"],
            "deaths": row["deaths"],
            "total_time_ms": row["total_time_ms"],
            "total_coins": row["total_coins"],
            "bronze_total": row["bronze_total"],
            "silver_total": row["silver_total"],
            "gold_total": row["gold_total"],
            "diamond_total": row["diamond_total"],
        }

        if all(value is None for value in stats_row.values()):
            stats = None
        else:
            class _Row(dict):
                pass

            stats = _row_to_aggregate_stats(
                _Row(stats_row)  # type: ignore[arg-type]
            )

        players.append(
            PlayerProfile(
                player_id=int(row["player_id"]),
                name=str(row["name"]),
                stats=stats,
            )
        )

    return players


def create_player(db_path: PathType, name: str) -> PlayerProfile:
    """
    Создаёт нового игрока с указанным именем и пустой статистикой.

    Если игрок с таким именем уже существует, возбуждает ValueError.

    :param db_path: путь к SQLite-файлу.
    :param name: имя игрока (уникальное, не пустое).
    :return: созданный PlayerProfile.
    """
    safe_name = name.strip()
    if not safe_name:
        raise ValueError("Имя игрока не может быть пустым.")

    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        try:
            try:
                cursor.execute(
                    "INSERT INTO players (name) VALUES (?);",
                    (safe_name,),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"Игрок с именем '{safe_name}' уже существует.") from exc

            player_id = int(cursor.lastrowid)

            cursor.execute(
                "INSERT INTO player_stats (player_id) VALUES (?);",
                (player_id,),
            )

            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()

    return PlayerProfile(
        player_id=player_id,
        name=safe_name,
        stats=PlayerAggregateStats(),
    )


def delete_player(db_path: PathType, player_id: int) -> None:
    """
    Удаляет игрока и всю его статистику из БД.

    Благодаря ON DELETE CASCADE в схеме:
        - запись из players;
        - связанная строка в player_stats;
        - все записи в runs для этого игрока
    удаляются автоматически.

    :param db_path: путь к SQLite-файлу.
    :param player_id: идентификатор игрока.
    :raises ValueError: если игрока с таким id не существует.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT 1 FROM players WHERE player_id = ?;", (player_id,))
            row = cursor.fetchone()
            if row is None:
                raise ValueError(f"Игрок с id={player_id} не найден в БД.")

            cursor.execute("DELETE FROM players WHERE player_id = ?;", (player_id,))
            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()


def get_player_by_name(db_path: PathType, name: str) -> Optional[PlayerProfile]:
    """
    Возвращает профиль игрока по имени или None, если его нет.

    :param db_path: путь к БД.
    :param name: имя игрока.
    :return: PlayerProfile или None.
    """
    safe_name = name.strip()
    if not safe_name:
        return None

    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    p.player_id,
                    p.name,
                    s.best_score,
                    s.best_time_ms,
                    s.max_coins,
                    s.total_runs,
                    s.wins,
                    s.deaths,
                    s.total_time_ms,
                    s.total_coins,
                    s.bronze_total,
                    s.silver_total,
                    s.gold_total,
                    s.diamond_total
                FROM players AS p
                LEFT JOIN player_stats AS s
                    ON s.player_id = p.player_id
                WHERE p.name = ?;
                """,
                (safe_name,),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()
    finally:
        connection.close()

    if row is None:
        return None

    stats_row = {
        "best_score": row["best_score"],
        "best_time_ms": row["best_time_ms"],
        "max_coins": row["max_coins"],
        "total_runs": row["total_runs"],
        "wins": row["wins"],
        "deaths": row["deaths"],
        "total_time_ms": row["total_time_ms"],
        "total_coins": row["total_coins"],
        "bronze_total": row["bronze_total"],
        "silver_total": row["silver_total"],
        "gold_total": row["gold_total"],
        "diamond_total": row["diamond_total"],
    }

    if all(value is None for value in stats_row.values()):
        stats = None
    else:
        class _Row(dict):
            pass

        stats = _row_to_aggregate_stats(
            _Row(stats_row)  # type: ignore[arg-type]
        )

    return PlayerProfile(
        player_id=int(row["player_id"]),
        name=str(row["name"]),
        stats=stats,
    )


def get_or_create_player(db_path: PathType, name: str) -> PlayerProfile:
    """
    Возвращает существующего игрока по имени или создаёт нового.

    :param db_path: путь к БД.
    :param name: имя игрока.
    :return: PlayerProfile.
    """
    existing = get_player_by_name(db_path, name)
    if existing is not None:
        return existing
    return create_player(db_path, name)
