from __future__ import annotations

"""
db_manager.py — работа с SQLite для Maze Game.

Назначение:
    - централизованно инициализировать базу данных (создать таблицы, включить PRAGMA);
    - получать соединение с БД с нужными настройками;
    - скрыть детали схемы от остального кода.

Схема БД:

    players:
        player_id   INTEGER PRIMARY KEY AUTOINCREMENT
        name        TEXT UNIQUE NOT NULL

    player_stats:
        player_id       INTEGER PRIMARY KEY REFERENCES players(player_id) ON DELETE CASCADE
        best_score      INTEGER NOT NULL DEFAULT 0
        best_time_ms    INTEGER                 -- минимальное время победы (NULL, если нет побед)
        max_coins       INTEGER NOT NULL DEFAULT 0
        total_runs      INTEGER NOT NULL DEFAULT 0
        wins            INTEGER NOT NULL DEFAULT 0
        deaths          INTEGER NOT NULL DEFAULT 0
        total_time_ms   INTEGER NOT NULL DEFAULT 0
        total_coins     INTEGER NOT NULL DEFAULT 0
        bronze_total    INTEGER NOT NULL DEFAULT 0
        silver_total    INTEGER NOT NULL DEFAULT 0
        gold_total      INTEGER NOT NULL DEFAULT 0
        diamond_total   INTEGER NOT NULL DEFAULT 0

    runs:
        run_id          INTEGER PRIMARY KEY AUTOINCREMENT
        player_id       INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE
        score           INTEGER NOT NULL
        elapsed_ms      INTEGER NOT NULL
        coins_value     INTEGER NOT NULL
        won             INTEGER NOT NULL        -- 0 или 1
        bronze_count    INTEGER NOT NULL
        silver_count    INTEGER NOT NULL
        gold_count      INTEGER NOT NULL
        diamond_count   INTEGER NOT NULL
        timestamp_utc   TEXT NOT NULL          -- ISO8601 в UTC

    meta:
        key             TEXT PRIMARY KEY
        value           TEXT NOT NULL

В этом модуле НЕТ логики игры, только инфраструктура БД.
"""

import os
import sqlite3
from typing import Sequence


PathType = str | os.PathLike[str]


def _apply_pragmas(connection: sqlite3.Connection) -> None:
    """
    Включает полезные PRAGMA для SQLite-подключения.

    - foreign_keys=ON  — гарантируем работу внешних ключей;
    - journal_mode=WAL — более дружелюбен к частым записям;
    - synchronous=NORMAL — компромисс надёжности и скорости.
    """
    cursor = connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        connection.commit()
    finally:
        cursor.close()


def get_connection(db_path: PathType) -> sqlite3.Connection:
    """
    Открывает соединение с SQLite по заданному пути и применяет PRAGMA.

    :param db_path: путь к файлу БД (str или PathLike).
    :return: объект sqlite3.Connection с row_factory=sqlite3.Row.
    """
    path_str = os.fspath(db_path)
    connection = sqlite3.connect(path_str)
    connection.row_factory = sqlite3.Row
    _apply_pragmas(connection)
    return connection


def _execute_schema_statements(
    connection: sqlite3.Connection,
    statements: Sequence[str],
) -> None:
    """
    Последовательно выполняет набор SQL-операторов создания схемы.

    :param connection: активное соединение SQLite.
    :param statements: список SQL-строк (CREATE TABLE/CREATE INDEX/...).
    """
    cursor = connection.cursor()
    try:
        for statement in statements:
            cursor.execute(statement)
        connection.commit()
    finally:
        cursor.close()


def init_db(db_path: PathType) -> None:
    """
    Создаёт (если нужно) и инициализирует базу данных Maze Game.

    Поведение:
        - если файл не существует, он будет создан;
        - таблицы создаются с помощью CREATE TABLE IF NOT EXISTS;
        - повторный вызов безопасен (схема стабилизируется, но не ломается).

    :param db_path: путь к файлу БД (str или PathLike).
    """
    schema_statements: list[str] = [
        # --- players: список игроков ---
        """
        CREATE TABLE IF NOT EXISTS players (
            player_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE
        );
        """,
        # --- player_stats: агрегированная статистика по игроку ---
        """
        CREATE TABLE IF NOT EXISTS player_stats (
            player_id       INTEGER PRIMARY KEY,
            best_score      INTEGER NOT NULL DEFAULT 0,
            best_time_ms    INTEGER,
            max_coins       INTEGER NOT NULL DEFAULT 0,
            total_runs      INTEGER NOT NULL DEFAULT 0,
            wins            INTEGER NOT NULL DEFAULT 0,
            deaths          INTEGER NOT NULL DEFAULT 0,
            total_time_ms   INTEGER NOT NULL DEFAULT 0,
            total_coins     INTEGER NOT NULL DEFAULT 0,
            bronze_total    INTEGER NOT NULL DEFAULT 0,
            silver_total    INTEGER NOT NULL DEFAULT 0,
            gold_total      INTEGER NOT NULL DEFAULT 0,
            diamond_total   INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE
        );
        """,
        # --- runs: отдельные забеги ---
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id       INTEGER NOT NULL,
            score           INTEGER NOT NULL,
            elapsed_ms      INTEGER NOT NULL,
            coins_value     INTEGER NOT NULL,
            won             INTEGER NOT NULL,
            bronze_count    INTEGER NOT NULL,
            silver_count    INTEGER NOT NULL,
            gold_count      INTEGER NOT NULL,
            diamond_count   INTEGER NOT NULL,
            timestamp_utc   TEXT NOT NULL,
            FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE
        );
        """,
        # индексы по runs: ускоряем выборки по игрокам и топам
        """
        CREATE INDEX IF NOT EXISTS idx_runs_player_id
            ON runs (player_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_runs_score
            ON runs (score DESC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_runs_timestamp
            ON runs (timestamp_utc DESC);
        """,
        # --- meta: служебные флаги (например, миграция из highscore.json) ---
        """
        CREATE TABLE IF NOT EXISTS meta (
            key     TEXT PRIMARY KEY,
            value   TEXT NOT NULL
        );
        """,
    ]

    connection = get_connection(db_path)
    try:
        _execute_schema_statements(connection, schema_statements)
    finally:
        connection.close()


def set_meta_flag(db_path: PathType, key: str, value: str) -> None:
    """
    Устанавливает (или обновляет) значение служебного флага в таблице meta.

    Пример использования:
        set_meta_flag("maze_stats.db", "highscore_migrated", "1")

    :param db_path: путь к БД.
    :param key: имя флага.
    :param value: строковое значение (например, "1", "true", версия схемы и т.д.).
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO meta (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value;
                """,
                (key, value),
            )
            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()


def get_meta_flag(db_path: PathType, key: str) -> str | None:
    """
    Возвращает значение служебного флага из таблицы meta или None, если записи нет.

    :param db_path: путь к БД.
    :param key: имя флага.
    :return: строковое значение или None.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT value FROM meta WHERE key = ?;", (key,))
            row = cursor.fetchone()
            if row is None:
                return None
            return str(row["value"])
        finally:
            cursor.close()
    finally:
        connection.close()
