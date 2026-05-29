from __future__ import annotations

"""
multiplayer_setup_state.py — настройка мультиплеерной очереди игроков.

Позволяет:
    - выбрать нескольких игроков, которые будут ходить по очереди;
    - создать новых игроков;
    - удалить игроков;
    - применить конфигурацию для режима RoundMode.ROTATE_QUEUE.

Управление:
    - ↑ / W — вверх
    - ↓ / S — вниз
    - Space — включить / выключить игрока в партии
    - N — создать нового игрока
    - Del / D — удалить игрока
    - A — выделить всех игроков
    - Enter — применить и вернуться в меню
    - Esc — отмена и возврат в меню
"""

from typing import Callable, Optional

import pygame

from .state_base import BaseState, StateManager
from domain.player_models import PlayerProfile
from session_controller import GameSessionController, RoundMode

from ui import get_text_font, get_emoji_font, render_mixed_text


class MultiplayerSetupState(BaseState):
    """
    Состояние настройки партии для мультиплеера по очереди.
    """

    def __init__(
        self,
        manager: StateManager,
        session: GameSessionController,
        *,
        on_done: Callable[[], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self.manager = manager
        self.session = session
        self.on_done = on_done
        self.on_cancel = on_cancel

        self.font_title: Optional[pygame.font.Font] = None
        self.font_entry: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None

        self.players: list[PlayerProfile] = []
        self.selected_index: int = 0

        # Список id игроков, включённых в очередь
        self.active_ids: list[int] = []

        # Режимы ввода
        self.name_input_active: bool = False
        self.name_input_buffer: str = ""
        self.name_input_error: Optional[str] = None

        self.delete_confirm_active: bool = False
        self.delete_error: Optional[str] = None

        # Ошибка при применении конфигурации
        self.apply_error: Optional[str] = None

        self.emoji_title: Optional[pygame.font.Font] = None
        self.emoji_entry: Optional[pygame.font.Font] = None
        self.emoji_small: Optional[pygame.font.Font] = None

        self.emoji_title: Optional[pygame.font.Font] = None
        self.emoji_entry: Optional[pygame.font.Font] = None
        self.emoji_small: Optional[pygame.font.Font] = None

        # Области строк игроков для наведения/кликов мышью
        self.player_row_rects: list[pygame.Rect] = []

    # ----------------- FSM lifecycle -----------------

    def enter(self) -> None:
        pygame.font.init()
        self.font_title = get_text_font(40)
        self.font_entry = get_text_font(26)
        self.font_small = get_text_font(18)

        self.emoji_title = get_emoji_font(40)
        self.emoji_entry = get_emoji_font(26)
        self.emoji_small = get_emoji_font(18)

        self._reload_players(initial=True)

    def exit(self) -> None:
        pass

    # ----------------- Events -----------------

    def handle_event(self, event: pygame.event.Event) -> None:
        # ПКМ: ведём себя как Esc — выходим из текущего режима/меню.
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if self.name_input_active:
                # Отмена ввода имени
                self.name_input_active = False
                self.name_input_buffer = ""
                self.name_input_error = None
            elif self.delete_confirm_active:
                # Отмена подтверждения удаления
                self.delete_confirm_active = False
                self.delete_error = None
            else:
                # Выход из состояния назад в меню
                self.on_cancel()
            return

        # Приоритет: режимы ввода
        if self.name_input_active:
            if event.type == pygame.KEYDOWN:
                self._handle_name_input_event(event)
            return

        if self.delete_confirm_active:
            if event.type == pygame.KEYDOWN:
                self._handle_delete_confirm_event(event)
            return

        # Наведение мыши по строкам игроков
        if event.type == pygame.MOUSEMOTION:
            if self.player_row_rects:
                for idx, rect in enumerate(self.player_row_rects):
                    if rect.collidepoint(event.pos):
                        if self.players:
                            self.selected_index = min(idx, len(self.players) - 1)
                        break
            return

        # ЛКМ по строке игрока — переключаем включён/выключен
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.player_row_rects and self.players:
                for idx, rect in enumerate(self.player_row_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_index = min(idx, len(self.players) - 1)
                        self._toggle_active_for_selected()
                        break
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.on_cancel()
        elif event.key in (pygame.K_UP, pygame.K_w):
            if self.players:
                self.selected_index = (self.selected_index - 1) % len(self.players)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            if self.players:
                self.selected_index = (self.selected_index + 1) % len(self.players)
        elif event.key == pygame.K_SPACE:
            self._toggle_active_for_selected()
        elif event.key == pygame.K_n:
            self._start_name_input()
        elif event.key in (pygame.K_DELETE, pygame.K_d):
            self._start_delete_confirm()
        elif event.key == pygame.K_a:
            self._select_all_players()
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._apply_configuration()

    # ----------------- Update -----------------

    def update(self, dt_ms: int) -> None:
        pass

    # ----------------- Render -----------------

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((10, 10, 20))

        assert self.font_title is not None
        assert self.font_entry is not None
        assert self.font_small is not None
        assert self.emoji_title is not None
        assert self.emoji_entry is not None
        assert self.emoji_small is not None

        width, height = screen.get_size()

        title = render_mixed_text(
            "👥 Настройка мультиплеера (очередь)",
            self.font_title,
            self.emoji_title,
        )
        title_rect = title.get_rect(center=(width // 2, 60))
        screen.blit(title, title_rect)

        mode_text = f"Текущий режим: {self._mode_label(self.session.mode)}"
        mode_surf = render_mixed_text(mode_text, self.font_small, self.emoji_small, (200, 200, 200))
        mode_rect = mode_surf.get_rect(center=(width // 2, 100))
        screen.blit(mode_surf, mode_rect)

        # Список игроков
        y = 150
        cursor_x = 60
        marker_x = 90
        name_x = 130

        self.player_row_rects = []

        for idx, profile in enumerate(self.players):
            is_cursor = idx == self.selected_index
            in_party = profile.player_id in self.active_ids

            color = (255, 220, 140) if is_cursor else (210, 210, 210)

            # 1) Курсор (стрелка) в отдельной колонке
            if is_cursor:
                cursor_surf = render_mixed_text("➡", self.font_entry, self.emoji_entry, color)
                cursor_rect = cursor_surf.get_rect(center=(cursor_x, y))
                screen.blit(cursor_surf, cursor_rect)

            # 2) Маркер участия в партии
            marker_char = "🟦" if in_party else "⬛"
            marker_surf = render_mixed_text(marker_char, self.font_entry, self.emoji_entry, color)
            marker_rect = marker_surf.get_rect(center=(marker_x, y))
            screen.blit(marker_surf, marker_rect)

            # 3) Имя игрока
            name_surf = render_mixed_text(profile.name, self.font_entry, self.emoji_entry, color)
            name_rect = name_surf.get_rect(midleft=(name_x, y))
            screen.blit(name_surf, name_rect)

            # Общая область строки для наведения/кликов
            row_height = 36
            row_rect = pygame.Rect(
                cursor_x,
                int(y - row_height / 2),
                width - cursor_x * 2,
                row_height,
            )
            self.player_row_rects.append(row_rect)

            y += 36

        # Подсказки
        hint_text = "Space — включить/выключить   N — новый   Del/D — удалить   A — все   Enter — применить   Esc — назад"
        hint = self.font_small.render(hint_text, True, (160, 160, 160))
        hint_rect = hint.get_rect(center=(width // 2, height - 30))
        screen.blit(hint, hint_rect)

        # Ошибка применения конфигурации
        if self.apply_error:
            err_surf = self.font_small.render(self.apply_error, True, (230, 80, 80))
            err_rect = err_surf.get_rect(center=(width // 2, height - 60))
            screen.blit(err_surf, err_rect)

        # Оверлеи
        if self.name_input_active:
            self._render_name_input_overlay(screen)
        if self.delete_confirm_active:
            self._render_delete_confirm_overlay(screen)

    # ----------------- Internal helpers -----------------

    @staticmethod
    def _mode_label(mode: RoundMode) -> str:
        if mode == RoundMode.SINGLE:
            return "Одиночный"
        if mode == RoundMode.ROTATE_QUEUE:
            return "По очереди"
        if mode == RoundMode.PICK_EACH_ROUND:
            return "Выбор игрока каждый раунд"
        return str(mode)

    def _reload_players(self, *, initial: bool = False) -> None:
        """
        Обновляет локальный список игроков и активный список.
        """
        self.players = list(self.session.players)

        if not self.players:
            raise RuntimeError("MultiplayerSetupState: нет ни одного игрока в сессии.")

        if initial:
            # По умолчанию — все игроки участвуют
            self.active_ids = [p.player_id for p in self.players]
        else:
            # Чистим active_ids от несуществующих
            valid_ids = {p.player_id for p in self.players}
            self.active_ids = [pid for pid in self.active_ids if pid in valid_ids]
            if not self.active_ids:
                self.active_ids = [self.players[0].player_id]

        if self.selected_index >= len(self.players):
            self.selected_index = len(self.players) - 1

    def _toggle_active_for_selected(self) -> None:
        if not self.players:
            return
        profile = self.players[self.selected_index]
        pid = profile.player_id
        if pid in self.active_ids:
            self.active_ids.remove(pid)
        else:
            self.active_ids.append(pid)

    def _select_all_players(self) -> None:
        self.active_ids = [p.player_id for p in self.players]

    # ---------- Новый игрок ----------

    def _start_name_input(self) -> None:
        self.name_input_active = True
        self.name_input_buffer = ""
        self.name_input_error = None
        self.apply_error = None

    def _handle_name_input_event(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            self.name_input_active = False
            self.name_input_buffer = ""
            self.name_input_error = None
            return

        if event.key == pygame.K_BACKSPACE:
            self.name_input_buffer = self.name_input_buffer[:-1]
            return

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._confirm_new_player()
            return

        char = event.unicode
        if not char:
            return
        if char.isprintable() and len(self.name_input_buffer) < 20:
            self.name_input_buffer += char

    def _confirm_new_player(self) -> None:
        name = self.name_input_buffer.strip()
        if not name:
            self.name_input_error = "Имя не может быть пустым."
            return

        try:
            profile = self.session.create_player(name)
        except ValueError as exc:
            self.name_input_error = str(exc)
            return

        self.name_input_active = False
        self.name_input_buffer = ""
        self.name_input_error = None
        self.apply_error = None

        # Обновляем локальный список и включаем нового игрока в партию
        self._reload_players(initial=False)
        self.active_ids.append(profile.player_id)
        self.selected_index = max(0, len(self.players) - 1)

    def _render_name_input_overlay(self, screen: pygame.Surface) -> None:
        assert self.font_entry is not None
        assert self.font_small is not None

        width, height = screen.get_size()

        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        box_width = width * 0.6
        box_height = 160
        box_x = (width - box_width) / 2
        box_y = (height - box_height) / 2

        rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, (245, 245, 245), rect, border_radius=10)
        pygame.draw.rect(screen, (80, 80, 80), rect, width=2, border_radius=10)

        title_surf = self.font_entry.render("Новый игрок", True, (0, 0, 0))
        title_rect = title_surf.get_rect(center=(width // 2, int(box_y + 30)))
        screen.blit(title_surf, title_rect)

        input_rect = pygame.Rect(
            box_x + 20,
            box_y + 60,
            box_width - 40,
            32,
        )
        pygame.draw.rect(screen, (255, 255, 255), input_rect, border_radius=5)
        pygame.draw.rect(screen, (120, 120, 120), input_rect, width=1, border_radius=5)

        display_text = self.name_input_buffer or "Введите имя..."
        color = (0, 0, 0) if self.name_input_buffer else (130, 130, 130)
        text_surf = self.font_small.render(display_text, True, color)
        text_rect = text_surf.get_rect(midleft=(input_rect.x + 8, input_rect.centery))
        screen.blit(text_surf, text_rect)

        if self.name_input_error:
            err_surf = self.font_small.render(self.name_input_error, True, (200, 60, 60))
            err_rect = err_surf.get_rect(
                center=(width // 2, int(box_y + box_height - 25)),
            )
            screen.blit(err_surf, err_rect)

    # ---------- Удаление игрока ----------

    def _start_delete_confirm(self) -> None:
        if not self.players:
            return
        self.delete_confirm_active = True
        self.delete_error = None
        self.apply_error = None

    def _handle_delete_confirm_event(self, event: pygame.event.Event) -> None:
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.delete_confirm_active = False
            self.delete_error = None
            return

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_y):
            self._confirm_delete_player()
            return

    def _confirm_delete_player(self) -> None:
        if not self.players:
            self.delete_confirm_active = False
            return

        profile = self.players[self.selected_index]
        try:
            self.session.delete_player_from_session(profile.player_id)
        except ValueError as exc:
            self.delete_error = str(exc)
            return

        # Успех
        self.delete_confirm_active = False
        self.delete_error = None
        self.apply_error = None
        self._reload_players(initial=False)

    def _render_delete_confirm_overlay(self, screen: pygame.Surface) -> None:
        assert self.font_entry is not None
        assert self.font_small is not None

        width, height = screen.get_size()

        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        box_width = width * 0.6
        box_height = 150
        box_x = (width - box_width) / 2
        box_y = (height - box_height) / 2

        rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, (245, 245, 245), rect, border_radius=10)
        pygame.draw.rect(screen, (120, 80, 80), rect, width=2, border_radius=10)

        player_name = self.players[self.selected_index].name if self.players else "—"
        title_text = f"Удалить игрока '{player_name}'?"
        title_surf = self.font_entry.render(title_text, True, (0, 0, 0))
        title_rect = title_surf.get_rect(center=(width // 2, int(box_y + 40)))
        screen.blit(title_surf, title_rect)

        hint_text = "Enter / Y — удалить   Esc — отмена"
        hint_surf = self.font_small.render(hint_text, True, (60, 60, 60))
        hint_rect = hint_surf.get_rect(center=(width // 2, int(box_y + box_height - 30)))
        screen.blit(hint_surf, hint_rect)

        if self.delete_error:
            err_surf = self.font_small.render(self.delete_error, True, (200, 60, 60))
            err_rect = err_surf.get_rect(center=(width // 2, int(box_y + box_height - 55)))
            screen.blit(err_surf, err_rect)

    # ---------- Применение конфигурации ----------

    def _apply_configuration(self) -> None:
        """
        Применяет выбранную конфигурацию игроков к сессии.
        """
        if not self.active_ids:
            self.apply_error = "Нужно выбрать хотя бы одного игрока."
            return

        try:
            self.session.configure_rotation_players(self.active_ids)
            self.session.set_mode(RoundMode.ROTATE_QUEUE)
        except ValueError as exc:
            self.apply_error = str(exc)
            return

        self.apply_error = None
        self.on_done()
