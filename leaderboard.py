from __future__ import annotations

"""
leaderboard.py — чтение статистики и лидерборда из SQLite для Maze Game.

Допускает использование:
    - в экранах статистики
    - в меню паузы / главном меню
    - для отображения прогресса игрока

НЕ зависит от pygame.
"""

import sqlite3
from dataclasses import dataclass
from typing import Optional, List

from db_manager import PathType, get_connection


# ============================
#  Датаклассы результатов
# ============================

@dataclass(frozen=True)
class RunEntry:
    """
    Представляет одну запись из таблицы runs — один забег.
    """
    run_id: int
    player_id: int
    player_name: str
    score: int
    elapsed_ms: int
    coins_value: int
    won: bool
    bronze: int
    silver: int
    gold: int
    diamond: int
    timestamp_utc: str


@dataclass(frozen=True)
class PlayerEntry:
    """
    Представляет агрегированную статистику игрока из player_stats.
    """
    player_id: int
    name: str
    best_score: int
    best_time_ms: Optional[int]
    max_coins: int
    total_runs: int
    wins: int
    deaths: int
    total_time_ms: int
    total_coins: int


# ============================
#  Вспомогальный селектор
# ============================

def _fetch_run_entries(cursor: sqlite3.Cursor) -> List[RunEntry]:
    """
    Преобразует все строки курсора в список RunEntry.
    """
    rows = cursor.fetchall()
    result: List[RunEntry] = []
    for r in rows:
        result.append(
            RunEntry(
                run_id=int(r["run_id"]),
                player_id=int(r["player_id"]),
                player_name=str(r["name"]),
                score=int(r["score"]),
                elapsed_ms=int(r["elapsed_ms"]),
                coins_value=int(r["coins_value"]),
                won=bool(r["won"]),
                bronze=int(r["bronze_count"]),
                silver=int(r["silver_count"]),
                gold=int(r["gold_count"]),
                diamond=int(r["diamond_count"]),
                timestamp_utc=str(r["timestamp_utc"]),
            )
        )
    return result


# ============================
#  API: Получение ТОПов
# ============================

def get_top_scores(db_path: PathType, limit: int = 10) -> List[RunEntry]:
    """
    Возвращает топ забегов по максимальному score.

    :param db_path: путь к SQLite-файлу.
    :param limit: сколько записей вернуть.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT
                    r.run_id, r.player_id, p.name,
                    r.score, r.elapsed_ms, r.coins_value, r.won,
                    r.bronze_count, r.silver_count, r.gold_count, r.diamond_count,
                    r.timestamp_utc
                FROM runs AS r
                JOIN players AS p ON p.player_id = r.player_id
                ORDER BY r.score DESC, r.elapsed_ms ASC
                LIMIT ?;
                """,
                (limit,),
            )
            return _fetch_run_entries(cur)
        finally:
            cur.close()
    finally:
        conn.close()


def get_best_times(db_path: PathType, limit: int = 10) -> List[RunEntry]:
    """
    Возвращает топ забегов по лучшему времени (только победы).

    :param db_path: путь к SQLite-файлу.
    :param limit: сколько записей вернуть.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT
                    r.run_id, r.player_id, p.name,
                    r.score, r.elapsed_ms, r.coins_value, r.won,
                    r.bronze_count, r.silver_count, r.gold_count, r.diamond_count,
                    r.timestamp_utc
                FROM runs AS r
                JOIN players AS p ON p.player_id = r.player_id
                WHERE r.won = 1
                ORDER BY r.elapsed_ms ASC
                LIMIT ?;
                """,
                (limit,),
            )
            return _fetch_run_entries(cur)
        finally:
            cur.close()
    finally:
        conn.close()


def get_top_coins(db_path: PathType, limit: int = 10) -> List[RunEntry]:
    """
    Возвращает топ забегов по суммарной ценности монет.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT
                    r.run_id, r.player_id, p.name,
                    r.score, r.elapsed_ms, r.coins_value, r.won,
                    r.bronze_count, r.silver_count, r.gold_count, r.diamond_count,
                    r.timestamp_utc
                FROM runs AS r
                JOIN players AS p ON p.player_id = r.player_id
                ORDER BY r.coins_value DESC, r.score DESC
                LIMIT ?;
                """,
                (limit,),
            )
            return _fetch_run_entries(cur)
        finally:
            cur.close()
    finally:
        conn.close()


# ============================
#  API: список игроков
# ============================

def get_players_sorted(db_path: PathType) -> List[PlayerEntry]:
    """
    Возвращает список всех игроков с агрегатами,
    отсортированный по best_score убыванию.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        try:
            cur.execute(
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
                    s.total_coins
                FROM players AS p
                LEFT JOIN player_stats AS s ON s.player_id = p.player_id
                ORDER BY s.best_score DESC;
                """
            )
            rows = cur.fetchall()
        finally:
            cur.close()
    finally:
        conn.close()

    result: List[PlayerEntry] = []
    for r in rows:
        result.append(
            PlayerEntry(
                player_id=int(r["player_id"]),
                name=str(r["name"]),
                best_score=int(r["best_score"]),
                best_time_ms=(int(r["best_time_ms"]) if r["best_time_ms"] is not None else None),
                max_coins=int(r["max_coins"]),
                total_runs=int(r["total_runs"]),
                wins=int(r["wins"]),
                deaths=int(r["deaths"]),
                total_time_ms=int(r["total_time_ms"]),
                total_coins=int(r["total_coins"]),
            )
        )
    return result


# ============================
#  API: агрегаты игрока
# ============================

def get_player_aggregate(db_path: PathType, player_id: int) -> Optional[PlayerEntry]:
    """
    Возвращает агрегированную статистику по конкретному игроку.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        try:
            cur.execute(
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
                    s.total_coins
                FROM players AS p
                LEFT JOIN player_stats AS s ON s.player_id = p.player_id
                WHERE p.player_id = ?;
                """,
                (player_id,),
            )
            row = cur.fetchone()
        finally:
            cur.close()
    finally:
        conn.close()

    if row is None:
        return None

    return PlayerEntry(
        player_id=int(row["player_id"]),
        name=str(row["name"]),
        best_score=int(row["best_score"]),
        best_time_ms=(int(row["best_time_ms"]) if row["best_time_ms"] is not None else None),
        max_coins=int(row["max_coins"]),
        total_runs=int(row["total_runs"]),
        wins=int(row["wins"]),
        deaths=int(row["deaths"]),
        total_time_ms=int(row["total_time_ms"]),
        total_coins=int(row["total_coins"]),
    )
