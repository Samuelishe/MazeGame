from __future__ import annotations

"""
mode_select_state.py — выбор режима игры для Maze Game.

Режимы:
    - Одиночный
    - Мультиплеер по очереди
    - Мультиплеер: выбор игрока каждый раунд
"""

from typing import Callable, Optional

import pygame

from .state_base import BaseState, StateManager
from session_controller import GameSessionController, RoundMode

from ui import get_text_font, get_emoji_font, render_mixed_text


class ModeSelectState(BaseState):
    """
    Состояние выбора режима игры.

    Изменяет режим в GameSessionController и возвращается
    в предыдущее меню через коллбэк.
    """

    def __init__(
        self,
        manager: StateManager,
        session: GameSessionController,
        *,
        on_exit_to_menu: Callable[[], None],
    ) -> None:
        self.manager = manager
        self.session = session
        self.on_exit_to_menu = on_exit_to_menu

        self.font_title: Optional[pygame.font.Font] = None
        self.font_entry: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None

        # Пункты меню: (текст, режим)
        self.options: list[tuple[str, RoundMode]] = [
            ("Одиночный", RoundMode.SINGLE),
            ("Мультиплеер: по очереди", RoundMode.ROTATE_QUEUE),
            ("Мультиплеер: выбор каждый раунд", RoundMode.PICK_EACH_ROUND),
        ]
        self.selected_index: int = 0

        self.emoji_title: Optional[pygame.font.Font] = None
        self.emoji_entry: Optional[pygame.font.Font] = None
        self.emoji_small: Optional[pygame.font.Font] = None

        self.emoji_title: Optional[pygame.font.Font] = None
        self.emoji_entry: Optional[pygame.font.Font] = None
        self.emoji_small: Optional[pygame.font.Font] = None

        # Области пунктов меню для наведения/кликов мышью
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

        # Выставляем выбранный пункт по текущему режиму
        current_mode = self.session.mode
        for idx, (_, mode) in enumerate(self.options):
            if mode == current_mode:
                self.selected_index = idx
                break

    def exit(self) -> None:
        pass

    # ----------------- Events -----------------

    def handle_event(self, event: pygame.event.Event) -> None:
        # ПКМ — назад в меню
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.on_exit_to_menu()
            return

        # Наведение мыши по пунктам
        if event.type == pygame.MOUSEMOTION:
            if self.option_rects:
                for idx, rect in enumerate(self.option_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_index = idx
                        break
            return

        # ЛКМ по пункту — применяем выбор
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.option_rects:
                for idx, rect in enumerate(self.option_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_index = idx
                        self._apply_selection()
                        break
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.on_exit_to_menu()
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.options)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.options)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._apply_selection()



    # ----------------- Update -----------------

    def update(self, dt_ms: int) -> None:
        pass

    # ----------------- Render -----------------

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((15, 15, 15))

        assert self.font_title is not None
        assert self.font_entry is not None
        assert self.font_small is not None
        assert self.emoji_title is not None
        assert self.emoji_entry is not None
        assert self.emoji_small is not None

        title_surf = render_mixed_text("⚙️ Режим игры", self.font_title, self.emoji_title)
        title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 80))
        screen.blit(title_surf, title_rect)

        y = 160
        self.option_rects = []

        for idx, (label, mode) in enumerate(self.options):
            is_selected = idx == self.selected_index
            color = (255, 220, 120) if is_selected else (210, 210, 210)

            label_with_emoji = self._decorate_option(label, mode)
            surf = render_mixed_text(
                label_with_emoji,
                self.font_entry,
                self.emoji_entry,
                color,
            )
            rect = surf.get_rect(center=(screen.get_width() // 2, y))

            self.option_rects.append(rect)
            screen.blit(surf, rect)

            y += 40

        hint = render_mixed_text(
            "Enter — выбрать   Esc — назад",
            self.font_small,
            self.emoji_small,
            (160, 160, 160),
        )
        hint_rect = hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
        screen.blit(hint, hint_rect)

    # ----------------- Internal -----------------

    def _apply_selection(self) -> None:
        _, mode = self.options[self.selected_index]
        self.session.set_mode(mode)
        self.on_exit_to_menu()

    @staticmethod
    def _decorate_option(label: str, mode: RoundMode) -> str:
        if mode == RoundMode.SINGLE:
            return "👤 " + label
        if mode == RoundMode.ROTATE_QUEUE:
            return "👥 " + label
        if mode == RoundMode.PICK_EACH_ROUND:
            return "🎲 " + label
        return label