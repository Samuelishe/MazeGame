from __future__ import annotations

"""
highscore_adapter.py — миграция рекордов из highscore.json в SQLite.

Назначение:
    - один раз прочитать существующий highscore.json;
    - создать технического игрока (например, "Игрок 1") в таблице players;
    - заполнить для него агрегированную статистику в player_stats;
    - добавить одну запись в runs, соответствующую лучшему забегу;
    - пометить факт миграции через meta.highscore_migrated.

После успешной миграции игра должна использовать SQLite для лидеров и
персональной статистики, а highscore.json может остаться как архив.
"""

import datetime as _dt
from typing import Optional

from db_manager import init_db, get_connection, get_meta_flag, set_meta_flag, PathType
from highscores import Highscore, load_highscore, default_path as highscore_default_path
from players import get_or_create_player


MIGRATION_FLAG_KEY = "highscore_migrated"


def _is_empty_highscore(hs: Highscore) -> bool:
    """
    Проверяет, содержит ли структура Highscore только значения по умолчанию.

    Используется, чтобы не создавать лишнюю запись в БД, если JSON пустой
    или никогда не заполнялся в реальной игре.
    """
    return (
        hs.best_score == 0
        and hs.max_coins_value == 0
        and hs.best_time_ms is None
        and hs.bronze_max == 0
        and hs.silver_max == 0
        and hs.gold_max == 0
        and hs.diamond_max == 0
    )


def _load_legacy_highscore() -> Optional[Highscore]:
    """
    Загружает рекорды из highscore.json через существующую логику highscores.py.

    :return:
        Highscore, если файл найден и в нём есть хоть какие-то данные;
        None, если файл отсутствует или содержит только значения по умолчанию.
    """
    hs_path = highscore_default_path()
    # load_highscore сам обрабатывает FileNotFoundError и битые файлы.
    hs = load_highscore(hs_path)
    if _is_empty_highscore(hs):
        return None
    return hs


def _insert_migrated_stats_for_player(
    db_path: PathType,
    player_id: int,
    hs: Highscore,
) -> None:
    """
    Записывает агрегированную статистику и одну запись забега для указанного игрока.

    Правила:
        - best_score, max_coins, best_time_ms переносятся напрямую;
        - считаем, что был хотя бы один забег → total_runs = 1;
        - если best_time_ms есть, считаем, что это победа → wins = 1, deaths = 0;
          иначе wins = 0, deaths = 1 (чтобы не было деления на ноль в будущих расчётах);
        - total_time_ms = best_time_ms или 0;
        - total_coins = max_coins_value;
        - *_total по монетам — такие же, как *_max;
        - в runs добавляется один забег с timestamp в UTC «сейчас».
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        try:
            best_time_ms = hs.best_time_ms if hs.best_time_ms is not None else 0
            won_flag = 1 if hs.best_time_ms is not None else 0
            deaths = 0 if won_flag == 1 else 1

            # Обновляем агрегаты в player_stats
            cursor.execute(
                """
                UPDATE player_stats
                SET
                    best_score    = ?,
                    best_time_ms  = ?,
                    max_coins     = ?,
                    total_runs    = ?,
                    wins          = ?,
                    deaths        = ?,
                    total_time_ms = ?,
                    total_coins   = ?,
                    bronze_total  = ?,
                    silver_total  = ?,
                    gold_total    = ?,
                    diamond_total = ?
                WHERE player_id = ?;
                """,
                (
                    hs.best_score,
                    hs.best_time_ms,
                    hs.max_coins_value,
                    1,  # total_runs
                    1 if won_flag == 1 else 0,
                    deaths,
                    best_time_ms,
                    hs.max_coins_value,
                    hs.bronze_max,
                    hs.silver_max,
                    hs.gold_max,
                    hs.diamond_max,
                    player_id,
                ),
            )

            # Добавляем одну запись в runs
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
                    player_id,
                    hs.best_score,
                    best_time_ms,
                    hs.max_coins_value,
                    won_flag,
                    hs.bronze_max,
                    hs.silver_max,
                    hs.gold_max,
                    hs.diamond_max,
                    timestamp_utc,
                ),
            )

            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()


def migrate_highscore_if_needed(
    db_path: PathType,
    *,
    legacy_player_name: str = "Игрок 1",
) -> None:
    """
    Выполняет миграцию рекордов из highscore.json в SQLite, если это ещё не делалось.

    Алгоритм:
        1. Инициализировать БД (init_db), чтобы были таблицы.
        2. Проверить meta.highscore_migrated:
            - если флаг есть, ничего не делаем;
        3. Попробовать загрузить highscore.json:
            - если файла нет или он пустой → отметить флагом "none" и выйти;
        4. Создать (или найти) игрока с именем legacy_player_name;
        5. Записать агрегаты и одну запись runs на базе данных из Highscore;
        6. Установить флаг meta.highscore_migrated = "1".

    :param db_path: путь к SQLite-файлу статистики.
    :param legacy_player_name: имя игрока, под которым будут сохранены старые рекорды.
    """
    # 1. Гарантируем наличие схемы
    init_db(db_path)

    # 2. Проверяем, не делали ли миграцию раньше
    already = get_meta_flag(db_path, MIGRATION_FLAG_KEY)
    if already is not None:
        return

    # 3. Пробуем загрузить JSON
    legacy_hs = _load_legacy_highscore()
    if legacy_hs is None:
        # Рекордов нет — помечаем и выходим.
        set_meta_flag(db_path, MIGRATION_FLAG_KEY, "none")
        return

    # 4. Находим/создаём игрока
    profile = get_or_create_player(db_path, legacy_player_name)

    # 5. Переносим агрегаты и одну запись забега
    _insert_migrated_stats_for_player(db_path, profile.player_id, legacy_hs)

    # 6. Ставим флаг миграции
    set_meta_flag(db_path, MIGRATION_FLAG_KEY, "1")
