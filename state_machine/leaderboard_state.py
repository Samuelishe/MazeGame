from __future__ import annotations

"""
leaderboard_state.py — экран лидерборда Maze Game.

Отображает:
    - таблицу лучших забегов (score)
    - список игроков с их лучшими результатами

Управление:
    - ↑/↓ — прокрутка списка (если он большой)
    - ESC / Backspace — выход в главное меню
    - ENTER / SPACE — тоже выход

Вся отрисовка — чистый pygame-рендер.
Логика данных — через leaderboard API.
"""

import pygame
from typing import Optional

from .state_base import BaseState, StateManager

from leaderboard import (
    get_top_scores,
    get_players_sorted,
    RunEntry,
    PlayerEntry,
)
from gameplay.formatting import format_time
from session_controller import GameSessionController

from ui import get_text_font, get_emoji_font, render_mixed_text

RUNS_VISIBLE_MAX: int = 10
PLAYERS_VISIBLE_MAX: int = 10

SCROLLBAR_WIDTH: int = 8
SCROLLBAR_MARGIN: int = 4


class LeaderboardState(BaseState):
    """
    Состояние отображения таблицы лидеров.

    Оно ничего не изменяет в БД — только читает данные.
    """

    def __init__(
        self,
        manager: StateManager,
        session: GameSessionController,
        *,
        on_exit_to_menu,
    ) -> None:
        self.manager = manager
        self.session = session
        self.on_exit_to_menu = on_exit_to_menu

        # ресурсы
        self.font_title: Optional[pygame.font.Font] = None
        self.font_entry: Optional[pygame.font.Font] = None

        # данные
        self.top_runs: list[RunEntry] = []
        self.players: list[PlayerEntry] = []

        self.emoji_title: Optional[pygame.font.Font] = None
        self.emoji_entry: Optional[pygame.font.Font] = None

        # прокрутка
        self.run_scroll: int = 0
        self.player_scroll: int = 0

        # области списков для определения зоны скролла и отрисовки скроллбаров
        self.runs_area: Optional[pygame.Rect] = None
        self.players_area: Optional[pygame.Rect] = None

        # геометрия ползунков и drag-состояние
        self.runs_thumb: Optional[pygame.Rect] = None
        self.players_thumb: Optional[pygame.Rect] = None
        self.drag_target: Optional[str] = None
        self.drag_offset_y: int = 0

    # ======================
    #   FSM Lifecycle
    # ======================

    def enter(self) -> None:
        pygame.font.init()
        self.font_title = get_text_font(40)
        self.font_entry = get_text_font(28)
        self.emoji_title = get_emoji_font(40)
        self.emoji_entry = get_emoji_font(28)

        # Загружаем данные из SQLite
        db_path = self.session.db_path
        self.top_runs = get_top_scores(db_path, limit=45)
        self.players = get_players_sorted(db_path)

    def exit(self) -> None:
        pass

    # ======================
    #   Event Handling
    # ======================

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            # ПКМ — назад в меню
            if event.button == 3:
                self.on_exit_to_menu()
                return

            # ЛКМ по ползунку — начинаем drag
            if event.button == 1:
                mouse_x, mouse_y = event.pos

                if self.runs_thumb is not None and self.runs_thumb.collidepoint(
                    mouse_x,
                    mouse_y,
                ):
                    self.drag_target = "runs"
                    self.drag_offset_y = mouse_y - self.runs_thumb.y
                    return

                if (
                    self.players_thumb is not None
                    and self.players_thumb.collidepoint(mouse_x, mouse_y)
                ):
                    self.drag_target = "players"
                    self.drag_offset_y = mouse_y - self.players_thumb.y
                    return

            # Колёсико мыши — скроллим либо верхний, либо нижний список
            if event.button in (4, 5):
                mouse_x, mouse_y = pygame.mouse.get_pos()

                target_runs = False
                target_players = True

                if self.runs_area is not None and self.runs_area.collidepoint(
                    mouse_x,
                    mouse_y,
                ):
                    target_runs = True
                    target_players = False
                elif (
                    self.players_area is not None
                    and self.players_area.collidepoint(mouse_x, mouse_y)
                ):
                    target_runs = False
                    target_players = True

                if target_runs:
                    max_scroll_runs = max(
                        0,
                        len(self.top_runs) - RUNS_VISIBLE_MAX,
                    )
                    if event.button == 4:  # wheel up
                        self.run_scroll = max(0, self.run_scroll - 1)
                    elif event.button == 5:  # wheel down
                        self.run_scroll = min(
                            max_scroll_runs,
                            self.run_scroll + 1,
                        )

                if target_players:
                    max_scroll_players = max(
                        0,
                        len(self.players) - PLAYERS_VISIBLE_MAX,
                    )
                    if event.button == 4:  # wheel up
                        self.player_scroll = max(0, self.player_scroll - 1)
                    elif event.button == 5:  # wheel down
                        self.player_scroll = min(
                            max_scroll_players,
                            self.player_scroll + 1,
                        )

                return

        # Завершаем drag
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.drag_target = None
            return

        # Перетаскивание ползунка
        if event.type == pygame.MOUSEMOTION and self.drag_target is not None:
            mouse_x, mouse_y = event.pos

            if (
                self.drag_target == "runs"
                and self.runs_area is not None
                and self.runs_thumb is not None
            ):
                area = self.runs_area
                thumb_height = self.runs_thumb.height
                max_scroll_runs = max(0, len(self.top_runs) - RUNS_VISIBLE_MAX)
                if max_scroll_runs > 0 and area.height > thumb_height:
                    max_offset = area.height - thumb_height
                    new_thumb_y = mouse_y - self.drag_offset_y
                    new_thumb_y = max(area.top, min(area.top + max_offset, new_thumb_y))
                    fraction = (new_thumb_y - area.top) / max_offset
                    self.run_scroll = int(round(fraction * max_scroll_runs))

            if (
                self.drag_target == "players"
                and self.players_area is not None
                and self.players_thumb is not None
            ):
                area = self.players_area
                thumb_height = self.players_thumb.height
                max_scroll_players = max(
                    0,
                    len(self.players) - PLAYERS_VISIBLE_MAX,
                )
                if max_scroll_players > 0 and area.height > thumb_height:
                    max_offset = area.height - thumb_height
                    new_thumb_y = mouse_y - self.drag_offset_y
                    new_thumb_y = max(area.top, min(area.top + max_offset, new_thumb_y))
                    fraction = (new_thumb_y - area.top) / max_offset
                    self.player_scroll = int(round(fraction * max_scroll_players))

            return

        # Клавиатура — только выход + скролл нижнего списка
        if event.type == pygame.KEYDOWN:
            if event.key in (
                pygame.K_ESCAPE,
                pygame.K_BACKSPACE,
                pygame.K_RETURN,
                pygame.K_SPACE,
            ):
                self.on_exit_to_menu()

            elif event.key in (pygame.K_UP, pygame.K_w):
                self.player_scroll = max(0, self.player_scroll - 1)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                max_scroll_players = max(
                    0,
                    len(self.players) - PLAYERS_VISIBLE_MAX,
                )
                self.player_scroll = min(
                    max_scroll_players,
                    self.player_scroll + 1,
                )



    # ======================
    #   Updating (not used)
    # ======================

    def update(self, dt_ms: int) -> None:
        pass

    # ======================
    #   Rendering
    # ======================

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((25, 25, 25))

        assert self.font_title is not None
        assert self.font_entry is not None
        assert self.emoji_title is not None
        assert self.emoji_entry is not None

        width, height = screen.get_size()

        # При каждой перерисовке сбрасываем геометрию ползунков
        self.runs_thumb = None
        self.players_thumb = None

        # ---- Заголовок ----
        title = render_mixed_text(
            "🏆 Лидерборд",
            self.font_title,
            self.emoji_title,
        )
        title_rect = title.get_rect(center=(width // 2, 60))
        screen.blit(title, title_rect)

        margin_x = 60
        line_height = 30
        scrollbar_space = SCROLLBAR_WIDTH + SCROLLBAR_MARGIN * 2

        # ---- ТОП забегов ----
        y = 130

        # Координаты столбцов для топа забегов
        rank_col_x = margin_x                      # номер + эмодзи + имя
        score_col_x = margin_x + 240               # очки (чуть ближе)
        time_col_x = margin_x + 410                # время
        coins_col_x = width - margin_x - scrollbar_space - 16  # монеты — с отступом от скроллбара

        header = render_mixed_text(
            "🥇 Топ забегов (Score):",
            self.font_entry,
            self.emoji_entry,
            (255, 220, 120),
        )
        header_rect = header.get_rect(
            midleft=(rank_col_x + 40, y),
        )
        screen.blit(header, header_rect)
        y += 50

        runs_y_start = y
        visible_runs = self.top_runs[
            self.run_scroll:self.run_scroll + RUNS_VISIBLE_MAX
        ]

        for idx, run in enumerate(visible_runs):
            global_rank = self.run_scroll + idx  # 0..24
            rank_number = global_rank + 1        # 1..25

            emoji = self._get_rank_emoji(global_rank)
            if emoji:
                left_text = f"{emoji} {rank_number:>2}. {run.player_name}"
            else:
                left_text = f"{rank_number:>2}. {run.player_name}"

            left_surf = render_mixed_text(
                left_text,
                self.font_entry,
                self.emoji_entry,
                (200, 200, 200),
            )
            left_rect = left_surf.get_rect(midleft=(rank_col_x, y))
            screen.blit(left_surf, left_rect)

            score_text = f"{run.score}"
            score_surf = self.font_entry.render(score_text, True, (200, 200, 200))
            score_rect = score_surf.get_rect(midleft=(score_col_x, y))
            screen.blit(score_surf, score_rect)

            time_text = format_time(run.elapsed_ms)
            time_surf = self.font_entry.render(time_text, True, (200, 200, 200))
            time_rect = time_surf.get_rect(midleft=(time_col_x, y))
            screen.blit(time_surf, time_rect)

            coins_text = f"балл ценностей: {run.coins_value}"
            coins_surf = self.font_entry.render(coins_text, True, (200, 200, 200))
            coins_rect = coins_surf.get_rect(midright=(coins_col_x, y))
            screen.blit(coins_surf, coins_rect)

            y += line_height

        runs_area_height = max(0, len(visible_runs) * line_height)
        if runs_area_height > 0:
            self.runs_area = pygame.Rect(
                margin_x,
                runs_y_start,
                width - margin_x * 2,
                runs_area_height,
            )
        else:
            self.runs_area = None

        self._draw_scrollbar(
            screen,
            self.runs_area,
            total_items=len(self.top_runs),
            visible_max=RUNS_VISIBLE_MAX,
            scroll_index=self.run_scroll,
        )

        # ---- Игроки ----
        y += 50

        header2 = self.font_entry.render(
            "Игроки:",
            True,
            (255, 220, 120),
        )
        header2_rect = header2.get_rect(midleft=(margin_x, y))
        screen.blit(header2, header2_rect)
        y += 50

        player_name_col_x = margin_x
        player_best_col_x = margin_x + 240
        player_wins_col_x = margin_x + 460
        player_time_col_x = width - margin_x - scrollbar_space - 16

        players_y_start = y
        visible_players = self.players[
            self.player_scroll:self.player_scroll + PLAYERS_VISIBLE_MAX
        ]

        for player in visible_players:
            name_surf = self.font_entry.render(
                player.name,
                True,
                (200, 200, 200),
            )
            name_rect = name_surf.get_rect(midleft=(player_name_col_x, y))
            screen.blit(name_surf, name_rect)

            best_text = f"лучший={player.best_score}"
            best_surf = self.font_entry.render(best_text, True, (200, 200, 200))
            best_rect = best_surf.get_rect(midleft=(player_best_col_x, y))
            screen.blit(best_surf, best_rect)

            wins_text = f"побед={player.wins}/{player.total_runs}"
            wins_surf = self.font_entry.render(wins_text, True, (200, 200, 200))
            wins_rect = wins_surf.get_rect(midleft=(player_wins_col_x, y))
            screen.blit(wins_surf, wins_rect)

            time_str = format_time(player.best_time_ms) if player.best_time_ms else "—"
            time_text = f"время={time_str}"
            time_surf = self.font_entry.render(time_text, True, (200, 200, 200))
            time_rect = time_surf.get_rect(midright=(player_time_col_x, y))
            screen.blit(time_surf, time_rect)

            y += line_height

        players_area_height = max(0, len(visible_players) * line_height)
        if players_area_height > 0:
            self.players_area = pygame.Rect(
                margin_x,
                players_y_start,
                width - margin_x * 2,
                players_area_height,
            )
        else:
            self.players_area = None

        self._draw_scrollbar(
            screen,
            self.players_area,
            total_items=len(self.players),
            visible_max=PLAYERS_VISIBLE_MAX,
            scroll_index=self.player_scroll,
        )

# --- Хелперы ---

    @staticmethod
    def _get_rank_emoji(global_rank: int) -> str:
        """
        Возвращает эмодзи для строки в таблице топа по её глобальному индексу.

        global_rank: 0-based индекс (0 — первое место, 44 — сорок пятое).
        """
        rank = global_rank + 1

        if rank == 1:
            return "🥇"
        if rank == 2:
            return "🥈"
        if rank == 3:
            return "🥉"
        if rank == 4:
            return "⭐"
        if rank == 5:
            return "⭐"
        if 6 <= rank <= 15:
            return "🟢"
        if 16 <= rank <= 25:
            return "🟡"
        if 26 <= rank <= 35:
            return "🟠"
        if 36 <= rank <= 45:
            return "🔴"
        return ""


    def _draw_scrollbar(
        self,
        screen: pygame.Surface,
        area: Optional[pygame.Rect],
        *,
        total_items: int,
        visible_max: int,
        scroll_index: int,
    ) -> None:
        """
        Рисует вертикальный скроллбар для указанной области.

        Появляется только если элементов больше, чем помещается на экране.
        Сохраняет геометрию ползунка для drag-обработки.
        """
        # Сбрасываем thumb, если области нет или скролл не нужен
        if area is None or total_items <= visible_max:
            if area is self.runs_area:
                self.runs_thumb = None
            if area is self.players_area:
                self.players_thumb = None
            return

        track_rect = pygame.Rect(
            area.right - SCROLLBAR_WIDTH,
            area.top,
            SCROLLBAR_WIDTH,
            area.height,
        )

        pygame.draw.rect(screen, (60, 60, 60), track_rect)

        max_scroll = max(0, total_items - visible_max)
        if max_scroll == 0:
            if area is self.runs_area:
                self.runs_thumb = None
            if area is self.players_area:
                self.players_thumb = None
            return

        thumb_height = max(
            12,
            area.height * visible_max // total_items,
        )

        max_offset = area.height - thumb_height
        offset = max_offset * scroll_index // max_scroll

        thumb_rect = pygame.Rect(
            track_rect.x,
            area.top + offset,
            SCROLLBAR_WIDTH,
            thumb_height,
        )
        pygame.draw.rect(screen, (220, 220, 220), thumb_rect)

        if area is self.runs_area:
            self.runs_thumb = thumb_rect
        elif area is self.players_area:
            self.players_thumb = thumb_rect

