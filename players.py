from __future__ import annotations

"""
players.py — сессионная статистика для Maze Game.

Содержит:
    - legacy compatibility re-export SessionStats;
    - временные re-export player repository API для совместимости импортов.

Этот модуль НЕ знает ничего про Pygame и игровую логику — только данные.
"""

from persistence.player_repository import (
    create_player,
    delete_player,
    get_or_create_player,
    get_player_by_name,
    load_players,
)
from runtime.session_stats import SessionStats

# Legacy compatibility shim during Stage 4:
# - repository imports are re-exported from persistence.player_repository;
# - SessionStats is re-exported from runtime.session_stats.
# This module should be cleaned up after compatibility imports are removed.
