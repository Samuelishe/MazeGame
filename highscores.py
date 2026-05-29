"""
highscores.py — хранение и обновление рекордов между запусками.

Сохраняем максимум очков, максимум монет, минимальное время (для побед),
и разбивку монет по редкостям (максимумы за попытку).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from json import JSONDecodeError
import json
import os
from typing import Optional


@dataclass
class Highscore:
    best_score: int = 0
    max_coins_value: int = 0
    best_time_ms: Optional[int] = None  # минимальное время победы
    bronze_max: int = 0
    silver_max: int = 0
    gold_max: int = 0
    diamond_max: int = 0


def default_path() -> str:
    """Путь к файлу рекордов рядом с этим модулем."""
    return os.path.join(os.path.dirname(__file__), "highscore.json")


def load_highscore(path: Optional[str] = None) -> Highscore:
    """
    Загружает рекорды из JSON. При отсутствии файла возвращает пустую структуру.
    """
    hs_path = path or default_path()
    try:
        with open(hs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Highscore(
            best_score=int(data.get("best_score", 0)),
            max_coins_value=int(data.get("max_coins_value", 0)),
            best_time_ms=(
                int(data["best_time_ms"]) if data.get("best_time_ms") is not None else None
            ),
            bronze_max=int(data.get("bronze_max", 0)),
            silver_max=int(data.get("silver_max", 0)),
            gold_max=int(data.get("gold_max", 0)),
            diamond_max=int(data.get("diamond_max", 0)),
        )
    except FileNotFoundError:
        return Highscore()
    except (OSError, JSONDecodeError, ValueError):
        # Файл битый — начинаем с чистого
        return Highscore()


def save_highscore(hs: Highscore, path: Optional[str] = None) -> None:
    """Сохраняет рекорды в JSON (безопасно, с utf-8)."""
    hs_path = path or default_path()
    tmp = hs_path + ".tmp"
    data = asdict(hs)
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, hs_path)
    except OSError:
        # Тихо игнорируем проблемы I/O — игра не должна падать из-за рекордов
        pass


def update_highscore_if_better(
    hs: Highscore,
    *,
    score: int,
    coins_value_sum: int,
    elapsed_ms: int,
    won: bool,
    bronze_count: int,
    silver_count: int,
    gold_count: int,
    diamond_count: int,
) -> bool:
    """
    Обновляет рекорды, если текущая попытка лучше предыдущих.
    Возвращает True, если что-то изменилось.
    Правила:
      - best_score — максимум;
      - max_coins_value — максимум;
      - best_time_ms — минимальное время среди побед;
      - *_max — максимумы одноразовых значений по редкостям.
    """
    changed = False

    if score > hs.best_score:
        hs.best_score = score
        changed = True

    if coins_value_sum > hs.max_coins_value:
        hs.max_coins_value = coins_value_sum
        changed = True

    if won:
        if hs.best_time_ms is None or elapsed_ms < hs.best_time_ms:
            hs.best_time_ms = elapsed_ms
            changed = True

    if bronze_count > hs.bronze_max:
        hs.bronze_max = bronze_count
        changed = True
    if silver_count > hs.silver_max:
        hs.silver_max = silver_count
        changed = True
    if gold_count > hs.gold_max:
        hs.gold_max = gold_count
        changed = True
    if diamond_count > hs.diamond_max:
        hs.diamond_max = diamond_count
        changed = True

    return changed
