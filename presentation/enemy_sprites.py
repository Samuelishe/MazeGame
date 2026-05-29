"""Enemy sprite loading and type mapping helpers."""

from __future__ import annotations

import pygame

from enemies import EnemyType
from sprites import SpriteSheet


def load_enemy_sheets_by_type() -> dict[EnemyType, SpriteSheet]:
    """
    Загружает спрайт-листы врагов и возвращает отображение типа врага в лист.

    Поведение сохранено из maze_game.py:
    - batch loading по фиксированному списку путей;
    - отсутствующие файлы пропускаются через pygame.error;
    - если не загрузилось вообще ничего, форсированно грузится красный слайм;
    - при частично отсутствующих ассетах недостающие индексы деградируют к
      первому успешно загруженному листу.
    """
    sprite_paths: list[str] = [
        "resources/images/enemies/Tiny_Slime Red.png",
        "resources/images/enemies/Tiny_Slime Green.png",
        "resources/images/enemies/Tiny_Slime Purple.png",
        "resources/images/enemies/Tiny_Slime Yellow.png",
    ]

    enemy_sheets: list[SpriteSheet] = []
    for path in sprite_paths:
        try:
            enemy_sheets.append(
                SpriteSheet.from_file(
                    path,
                    (16, 16),
                    spacing=(8, 8),
                    margin=(4, 4),
                )
            )
        except pygame.error:
            continue

    if not enemy_sheets:
        enemy_sheets.append(
            SpriteSheet.from_file(
                "resources/images/enemies/Tiny_Slime Red.png",
                (16, 16),
                spacing=(8, 8),
                margin=(4, 4),
            )
        )

    def sheet_or_default(index: int) -> SpriteSheet:
        return enemy_sheets[index] if index < len(enemy_sheets) else enemy_sheets[0]

    return {
        EnemyType.SLIME: sheet_or_default(1),
        EnemyType.MEDIUM: sheet_or_default(3),
        EnemyType.HUNTER: sheet_or_default(0),
        EnemyType.PATROLLER: sheet_or_default(2),
    }
