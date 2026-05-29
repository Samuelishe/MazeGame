from __future__ import annotations

"""
players.py — модель игрока и сессионная статистика для Maze Game.

Содержит:
    - PlayerAggregateStats — агрегированная статистика по игроку из БД;
    - PlayerProfile — профиль игрока (id, имя, агрегаты);
    - функции работы с таблицами players / player_stats;
    - SessionStats — сессионная статистика в ОЗУ (за текущий запуск игры).

Этот модуль НЕ знает ничего про Pygame и игровую логику — только данные.
"""

from dataclasses import dataclass
import os
import sqlite3
from typing import Optional

from db_manager import get_connection


PathType = str | os.PathLike[str]


# ---------- Агрегаты игрока (из БД) ----------


@dataclass
class PlayerAggregateStats:
    """
    Агрегированная статистика по игроку из таблицы player_stats.

    best_score:
        Лучший результат по очкам.
    best_time_ms:
        Минимальное время победы в миллисекундах (None, если побед не было).
    max_coins:
        Максимальная суммарная ценность монет за один забег.
    total_runs:
        Общее количество попыток.
    wins / deaths:
        Количество побед и поражений.
    total_time_ms:
        Суммарное игровое время (по всем попыткам).
    total_coins:
        Суммарная ценность монет по всем попыткам.
    *_total:
        Общее количество собранных монет каждой редкости.
    """

    best_score: int = 0
    best_time_ms: Optional[int] = None
    max_coins: int = 0
    total_runs: int = 0
    wins: int = 0
    deaths: int = 0
    total_time_ms: int = 0
    total_coins: int = 0
    bronze_total: int = 0
    silver_total: int = 0
    gold_total: int = 0
    diamond_total: int = 0


@dataclass
class PlayerProfile:
    """
    Профиль игрока в Maze Game.

    player_id:
        Идентификатор в таблице players.
    name:
        Имя игрока (уникально).
    stats:
        Агрегированная статистика из player_stats, если есть.
    """

    player_id: int
    name: str
    stats: Optional[PlayerAggregateStats] = None


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

        # Если в stats всё None — агрегатов пока нет.
        if all(value is None for value in stats_row.values()):
            stats = None
        else:
            # Отдельный Row уже не нужен, собираем временный словарь.
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
                # Уникальный индекс по имени уже сработал
                raise ValueError(f"Игрок с именем '{safe_name}' уже существует.") from exc

            player_id = int(cursor.lastrowid)

            # Создаём строку в player_stats с дефолтами
            cursor.execute(
                "INSERT INTO player_stats (player_id) VALUES (?);",
                (player_id,),
            )

            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()

    # Только что созданный игрок, статистика — пустая
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


# ---------- Сессионная статистика в ОЗУ (SessionStats) ----------


@dataclass
class SessionStats:
    """
    Счётчики текущей игровой сессии (пока процесс не закрыт):

    - runs: количество попыток;
    - wins / deaths: победы и поражения;
    - total_score: суммарные очки;
    - total_time_ms: суммарное время;
    - total_coins: суммарная ценность монет;
    - *_total: общий счётчик монет по редкостям.

    Эта статистика живёт только в памяти и не связана напрямую с БД.
    """

    runs: int = 0
    wins: int = 0
    deaths: int = 0
    total_score: int = 0
    total_time_ms: int = 0
    total_coins: int = 0

    bronze_total: int = 0
    silver_total: int = 0
    gold_total: int = 0
    diamond_total: int = 0

    def add_result(
        self,
        *,
        won: bool,
        coins_value_sum: int,
        elapsed_ms: int,
        score: int,
        bronze_count: int,
        silver_count: int,
        gold_count: int,
        diamond_count: int,
    ) -> None:
        """
        Обновляет агрегированные значения по результату одного забега.

        :param won: True, если забег завершился победой.
        :param coins_value_sum: сумма номиналов монет за попытку.
        :param elapsed_ms: длительность забега в миллисекундах.
        :param score: финальный счёт.
        :param bronze_count: количество бронзовых монет за забег.
        :param silver_count: количество серебряных монет за забег.
        :param gold_count: количество золотых монет за забег.
        :param diamond_count: количество бриллиантов за забег.
        """
        self.runs += 1
        self.total_coins += coins_value_sum
        self.total_time_ms += elapsed_ms
        self.total_score += score

        self.bronze_total += bronze_count
        self.silver_total += silver_count
        self.gold_total += gold_count
        self.diamond_total += diamond_count

        if won:
            self.wins += 1
        else:
            self.deaths += 1

    def summary_line(self) -> str:
        """
        Возвращает краткую сводку по сессии одной строкой для HUD/оверлея.

        Пример:
            "Сессия: попыток 5 • побед 2 • смертей 3 • очки 1234 • "
            "ценность монет 17 • ср. время 1:12.345 • 🥉7 • 🥈6 • 🥇3 • 💎1"
        """
        avg_time_ms = self.total_time_ms // max(1, self.runs)
        base = (
            f"Сессия: попыток {self.runs} • побед {self.wins} • смертей {self.deaths} • "
            f"очки {self.total_score} • ценность монет {self.total_coins} • "
            f"ср. время {self._format_time(avg_time_ms)}"
        )
        by_types = (
            f" • 🥉{self.bronze_total} • 🥈{self.silver_total} • "
            f"🥇{self.gold_total} • 💎{self.diamond_total}"
        )
        return base + by_types

    @staticmethod
    def _format_time(ms: int) -> str:
        """
        Локальная версия форматирования времени:
        М:SS.мс, например 1:23.456
        """
        seconds, msec = divmod(ms, 1000)
        minutes, sec = divmod(seconds, 60)
        return f"{minutes}:{sec:02d}.{msec:03d}"
