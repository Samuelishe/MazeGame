from __future__ import annotations

"""
player_select_state.py — экран выбора игрока для Maze Game.

Позволяет:
    - просмотреть список игроков;
    - выбрать активного игрока;
    - создать нового игрока;
    - вернуться в главное меню.

Управление:
    - ↑ / W — вверх
    - ↓ / S — вниз
    - Enter / Space — выбрать игрока
    - N — создать нового игрока
    - Esc / Backspace — отмена и возврат в меню

В режиме ввода имени:
    - печать символов — ввод имени
    - Backspace — удалить символ
    - Enter — создать игрока
    - Esc — отмена создания
"""

from typing import Callable, Optional

import pygame

from .state_base import BaseState, StateManager
from domain.player_models import PlayerProfile
from session_controller import GameSessionController

from ui import get_text_font, get_emoji_font, render_mixed_text


class PlayerSelectState(BaseState):
    """
    Состояние выбора игрока.

    Позволяет выбрать активного игрока из списка существующих
    или создать нового игрока по имени.

    Непосредственно запись в БД выполняет GameSessionController.
    """

    def __init__(
        self,
        manager: StateManager,
        session: GameSessionController,
        *,
        on_selected: Callable[[], None],
        on_cancel: Callable[[], None],

    ) -> None:
        self.manager = manager
        self.session = session
        self.on_selected = on_selected
        self.on_cancel = on_cancel

        self.font_title: Optional[pygame.font.Font] = None
        self.font_entry: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None

        self.players: list[PlayerProfile] = []
        self.selected_index: int = 0

        # Режим ввода имени нового игрока
        self.name_input_active: bool = False
        self.name_input_buffer: str = ""
        self.name_input_error: Optional[str] = None

        # Режим подтверждения удаления игрока
        self.delete_confirm_active: bool = False
        self.delete_error: Optional[str] = None

        self.emoji_title: Optional[pygame.font.Font] = None
        self.emoji_entry: Optional[pygame.font.Font] = None
        self.emoji_small: Optional[pygame.font.Font] = None

        self.emoji_title: Optional[pygame.font.Font] = None
        self.emoji_entry: Optional[pygame.font.Font] = None
        self.emoji_small: Optional[pygame.font.Font] = None

        # Области строк игроков для навигации мышью
        self.option_rects: list[pygame.Rect] = []

    # ----------------- FSM lifecycle -----------------

    def enter(self) -> None:
        pygame.font.init()
        self.font_title = get_text_font(40)
        self.font_entry = get_text_font(28)
        self.font_small = get_text_font(20)

        self.emoji_title = get_emoji_font(40)
        self.emoji_entry = get_emoji_font(28)
        self.emoji_small = get_emoji_font(20)

        self._reload_players()

    def exit(self) -> None:
        pass

    # ----------------- Events -----------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Обрабатывает события для экрана выбора игрока.

        Поддерживает:
        - мышь (ПКМ как Esc, наведение/клик по игроку);
        - клавиатуру (стрелки / WASD, Enter/Space, N, Delete, Esc);
        - отдельные режимы ввода имени и подтверждения удаления.
        """
        # ПКМ: ведём себя как Esc
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if self.name_input_active:
                # Отмена создания нового игрока
                self.name_input_active = False
                self.name_input_buffer = ""
                self.name_input_error = None
            elif self.delete_confirm_active:
                # Отмена подтверждения удаления
                self.delete_confirm_active = False
                self.delete_error = None
            else:
                # Выход из экрана выбора игрока
                self.on_cancel()
            return

        # ----- Режим ввода имени нового игрока -----
        if self.name_input_active:
            if event.type == pygame.KEYDOWN:
                self._handle_name_input_event(event)
            return

        # ----- Режим подтверждения удаления -----
        if self.delete_confirm_active:
            if event.type == pygame.KEYDOWN:
                self._handle_delete_confirm_event(event)
            return

        # ----- Навигация мышью по списку игроков -----
        if event.type == pygame.MOUSEMOTION:
            if self.option_rects:
                for idx, rect in enumerate(self.option_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_index = idx
                        break
            return

        # ЛКМ по игроку — сразу выбираем его
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.option_rects:
                for idx, rect in enumerate(self.option_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_index = idx
                        self._apply_selection()
                        break
            return

        # ----- Обычный режим: работаем только с KEYDOWN -----
        if event.type != pygame.KEYDOWN:
            return

        key = event.key

        # Стрелки / WASD — навигация по списку игроков
        if key in (pygame.K_UP, pygame.K_w):
            if self.players:
                self.selected_index = (self.selected_index - 1) % len(self.players)
            return

        if key in (pygame.K_DOWN, pygame.K_s):
            if self.players:
                self.selected_index = (self.selected_index + 1) % len(self.players)
            return

        # Enter / Space — выбрать текущего игрока
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if self.players:
                self._apply_selection()
            return

        # Esc / Backspace — выйти назад в меню
        if key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.on_cancel()
            return

        # N — начать создание нового игрока
        if key == pygame.K_n:
            self._start_name_input()
            return

        # Delete / D — удалить игрока (с подтверждением)
        if key in (pygame.K_DELETE, pygame.K_d):
            self._start_delete_confirm()
            return



    # ----------------- Update -----------------

    def update(self, dt_ms: int) -> None:
        # Логика этого состояния не зависит от времени.
        pass

    # ----------------- Render -----------------

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((20, 20, 20))

        assert self.font_title is not None
        assert self.font_entry is not None
        assert self.font_small is not None
        assert self.emoji_title is not None
        assert self.emoji_entry is not None
        assert self.emoji_small is not None

        title = render_mixed_text("🙂 Выбор игрока", self.font_title, self.emoji_title)
        title_rect = title.get_rect(center=(screen.get_width() // 2, 80))
        screen.blit(title, title_rect)

        # Список игроков
        y = 150
        self.option_rects = []

        for idx, profile in enumerate(self.players):
            is_selected = idx == self.selected_index
            color = (255, 220, 120) if is_selected else (210, 210, 210)

            text = profile.name
            if profile.stats is not None:
                text += f"  — лучший счёт: {profile.stats.best_score}"

            surf = render_mixed_text(
                text,
                self.font_entry,
                self.emoji_entry,
                color,
            )
            rect = surf.get_rect(center=(screen.get_width() // 2, y))

            self.option_rects.append(rect)
            screen.blit(surf, rect)

            y += 40

        # Подсказка
        hint_text = "Enter — выбрать   Esc — назад   N — новый игрок   Del/D — удалить"
        hint = render_mixed_text(hint_text, self.font_small, self.emoji_small, (160, 160, 160))
        hint_rect = hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
        screen.blit(hint, hint_rect)

        # Если активен режим ввода имени — рисуем оверлей
        if self.name_input_active:
            self._render_name_input_overlay(screen)

        # Оверлей подтверждения удаления
        if self.delete_confirm_active:
            self._render_delete_confirm_overlay(screen)

    # ----------------- Internal: базовые операции -----------------

    def _reload_players(self) -> None:
        """
        Обновляет локальный список игроков и выбранный индекс
        в соответствии с текущим игроком в контроллере.
        """
        self.players = list(self.session.players)

        if not self.players:
            raise RuntimeError("PlayerSelectState: нет ни одного игрока в сессии.")

        current = self.session.current_player()
        for idx, profile in enumerate(self.players):
            if profile.player_id == current.player_id:
                self.selected_index = idx
                break
        else:
            self.selected_index = 0

    def _apply_selection(self) -> None:
        profile = self.players[self.selected_index]
        self.session.choose_player(profile.player_id)
        self.on_selected()

    # ----------------- Internal: создание нового игрока -----------------

    def _start_name_input(self) -> None:
        """
        Переводит состояние в режим ввода имени нового игрока.
        """
        self.name_input_active = True
        self.name_input_buffer = ""
        self.name_input_error = None

    def _handle_name_input_event(self, event: pygame.event.Event) -> None:
        """
        Обрабатывает события в режиме ввода имени.
        """
        if event.key == pygame.K_ESCAPE:
            # Отмена создания
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

        # Добавление символов (ограниченно разумным набором)
        char = event.unicode
        if not char:
            return

        if char.isprintable() and len(self.name_input_buffer) < 20:
            self.name_input_buffer += char

    def _confirm_new_player(self) -> None:
        """
        Пытается создать нового игрока с введённым именем.
        """
        name = self.name_input_buffer.strip()
        if not name:
            self.name_input_error = "Имя не может быть пустым."
            return

        try:
            profile = self.session.create_player(name)
        except ValueError as exc:
            # Например, если игрок с таким именем уже существует.
            self.name_input_error = str(exc)
            return

        # Успех: сбрасываем режим ввода, выбираем игрока и выходим через on_selected.
        self.name_input_active = False
        self.name_input_buffer = ""
        self.name_input_error = None

        self.session.choose_player(profile.player_id)
        self.on_selected()

    def _render_name_input_overlay(self, screen: pygame.Surface) -> None:
        """
        Рисует оверлей для ввода имени нового игрока.
        """
        assert self.font_title is not None
        assert self.font_entry is not None
        assert self.font_small is not None

        width, height = screen.get_size()

        # Полупрозрачный фон
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

        # Поле ввода
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

        # Ошибка, если есть
        if self.name_input_error:
            err_surf = self.font_small.render(self.name_input_error, True, (200, 60, 60))
            err_rect = err_surf.get_rect(
                center=(width // 2, int(box_y + box_height - 30)),
            )
            screen.blit(err_surf, err_rect)

    # ----------------- Internal: удаление игрока -----------------

    def _start_delete_confirm(self) -> None:
        """
        Переводит состояние в режим подтверждения удаления текущего игрока.
        """
        if not self.players:
            return
        self.delete_confirm_active = True
        self.delete_error = None

    def _handle_delete_confirm_event(self, event: pygame.event.Event) -> None:
        """
        Обрабатывает нажатия клавиш в режиме подтверждения удаления.
        """
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            # Отмена удаления
            self.delete_confirm_active = False
            self.delete_error = None
            return

        if event.key in (pygame.K_RETURN, pygame.K_y, pygame.K_KP_ENTER):
            self._confirm_delete_player()
            return

    def _confirm_delete_player(self) -> None:
        """
        Пытается удалить выбранного игрока через GameSessionController.
        """
        if not self.players:
            self.delete_confirm_active = False
            return

        profile = self.players[self.selected_index]
        try:
            self.session.delete_player_from_session(profile.player_id)
        except ValueError as exc:
            # Например, попытка удалить последнего игрока
            self.delete_error = str(exc)
            return

        # Успех: обновляем список игроков и выходим из режима подтверждения.
        self.delete_confirm_active = False
        self.delete_error = None
        self._reload_players()

    def _render_delete_confirm_overlay(self, screen: pygame.Surface) -> None:
        """
        Рисует оверлей подтверждения удаления игрока.
        """
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

