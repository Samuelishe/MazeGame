from __future__ import annotations

"""
main_menu.py — главное меню игры Maze Game.

Показывает:
    - логотип / название игры
    - строку статуса (режим + текущий игрок)
    - случайную цитату
    - пункты меню:
        * Начать игру
        * Лидерборд
        * Сменить игрока (опционально)
        * Режим игры (опционально)
        * Мультиплеер (очередь) (опционально)
        * Выход

Это независимое состояние — оно НЕ знает про pygame-loop,
state manager сам передаёт события / update / render.
"""

from typing import Callable, Optional
import os

import pygame

from .state_base import BaseState, StateManager
from ui import get_text_font, get_emoji_font, render_mixed_text


class MainMenuState(BaseState):
    """
    Состояние главного меню.

    Поддерживает:
        - управление клавиатурой и мышью,
        - отображение статуса (режим / игрок),
        - отображение случайной цитаты,
        - лёгкую анимацию появления меню (fade-in + slide-up),
        - фон в виде текстуры (menu_background.png).
    """

    def __init__(
        self,
        manager: StateManager,
        *,
        status_line: Optional[str] = None,
        quote_text: Optional[str] = None,
        on_start_game: Callable[[], None],
        on_show_leaderboard: Callable[[], None],
        on_change_player: Optional[Callable[[], None]] = None,
        on_change_mode: Optional[Callable[[], None]] = None,
        on_setup_multiplayer: Optional[Callable[[], None]] = None,
        on_exit: Callable[[], None],
        quote_color: Optional[tuple[int, int, int]] = None,
    ) -> None:
        self.manager = manager

        # callbacks
        self.on_start_game = on_start_game
        self.on_show_leaderboard = on_show_leaderboard
        self.on_change_player = on_change_player
        self.on_change_mode = on_change_mode
        self.on_setup_multiplayer = on_setup_multiplayer
        self.on_exit = on_exit

        # статус и цитата под заголовком
        self.status_line = status_line
        self.quote_text = quote_text
        self.quote_color = quote_color or (150, 150, 150)

        # список опций меню
        self.options = ["Начать игру", "Лидерборд"]

        if self.on_change_player is not None:
            self.options.append("Сменить игрока")

        if self.on_change_mode is not None:
            self.options.append("Режим игры")

        if self.on_setup_multiplayer is not None:
            self.options.append("Мультиплеер (очередь)")

        self.options.append("Выход")

        self.selected_index: int = 0

        # шрифты
        self.font_title: Optional[pygame.font.Font] = None
        self.font_menu: Optional[pygame.font.Font] = None
        self.font_status: Optional[pygame.font.Font] = None
        self.font_quote: Optional[pygame.font.Font] = None

        # emoji-шрифты
        self.emoji_title: Optional[pygame.font.Font] = None
        self.emoji_menu: Optional[pygame.font.Font] = None
        self.emoji_status: Optional[pygame.font.Font] = None
        self.emoji_quote: Optional[pygame.font.Font] = None

        # прямоугольники пунктов меню для наведения/кликов мышью
        self.option_rects: list[pygame.Rect] = []

        # анимация меню
        self.menu_anim_time_ms: int = 0
        self.menu_anim_duration_ms: int = 350

        # фоновые текстуры меню
        self.background_image: Optional[pygame.Surface] = None
        self.background_scaled: Optional[pygame.Surface] = None
        self.background_scaled_size: Optional[tuple[int, int]] = None

        # логотип в верхней части меню
        self.logo_image: Optional[pygame.Surface] = None
        self.logo_scaled: Optional[pygame.Surface] = None
        self.logo_scaled_size: Optional[tuple[int, int]] = None

    # -------------------------------
    #   FSM Lifecycle
    # -------------------------------

    def enter(self) -> None:
        """Готовит ресурсы меню (шрифты, фон) и сбрасывает анимацию."""
        pygame.font.init()
        self.font_title = get_text_font(48)
        self.font_menu = get_text_font(32)
        self.font_status = get_text_font(22)
        self.font_quote = get_text_font(20)

        self.emoji_title = get_emoji_font(48)
        self.emoji_menu = get_emoji_font(32)
        self.emoji_status = get_emoji_font(22)
        self.emoji_quote = get_emoji_font(20)

        self.menu_anim_time_ms = 0

        self._load_background()
        self._load_logo()

    def exit(self) -> None:
        """При выходе ничего особенного делать не нужно."""
        pass

    # -------------------------------
    #   Event handling
    # -------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.options)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.options)

            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate_option()

            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.on_exit()

        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._handle_mouse_click(event.pos)
            elif event.button == 3:
                # правый клик в главном меню — тоже выход
                self.on_exit()

    # -------------------------------
    #   Updating
    # -------------------------------

    def update(self, dt_ms: int) -> None:
        """
        Обновляет состояние анимации меню.

        dt_ms:
            Время с прошлого кадра в миллисекундах.
        """
        if self.menu_anim_time_ms < self.menu_anim_duration_ms:
            self.menu_anim_time_ms = min(
                self.menu_anim_time_ms + dt_ms,
                self.menu_anim_duration_ms,
            )

    # -------------------------------
    #   Rendering
    # -------------------------------

    def render(self, screen: pygame.Surface) -> None:
        """Рисует фон, заголовок, статус, цитату и пункты меню."""
        self._render_background(screen)

        assert self.font_title is not None
        assert self.font_menu is not None
        assert self.font_status is not None
        assert self.font_quote is not None

        assert self.emoji_title is not None
        assert self.emoji_menu is not None
        assert self.emoji_status is not None
        assert self.emoji_quote is not None

        width, height = screen.get_size()

        # ============ Заголовок / логотип ============
        title_bottom = self._render_logo(screen)
        # Делаем нормальный зазор между логотипом и статусом/цитатой
        current_y = title_bottom + 40

        # ============ Статус + цитата с мягкой подложкой ============
        header_items: list[tuple[pygame.Surface, pygame.Rect]] = []

        # Статус
        if self.status_line:
            status_surface = render_mixed_text(
                self.status_line,
                self.font_status,
                self.emoji_status,
                (185, 185, 185),
            )
            status_rect = status_surface.get_rect(center=(width // 2, current_y))
            header_items.append((status_surface, status_rect))
            current_y = status_rect.bottom + 6

        # Цитата
        if self.quote_text:
            quote_surface = render_mixed_text(
                self.quote_text,
                self.font_quote,
                self.emoji_quote,
                self.quote_color,
            )
            quote_rect = quote_surface.get_rect(center=(width // 2, current_y))
            header_items.append((quote_surface, quote_rect))
            current_y = quote_rect.bottom + 25
        else:
            if not header_items:
                current_y += 20
            else:
                current_y += 10

        # Рисуем нежную подложку под статус+цитату
        if header_items:
            min_left = min(rect.left for _, rect in header_items)
            max_right = max(rect.right for _, rect in header_items)
            min_top = min(rect.top for _, rect in header_items)
            max_bottom = max(rect.bottom for _, rect in header_items)

            padding_x = 24
            padding_y = 10

            backdrop_left = max(0, min_left - padding_x)
            backdrop_top = max(0, min_top - padding_y)
            backdrop_right = min(width, max_right + padding_x)
            backdrop_bottom = min(height, max_bottom + padding_y)

            backdrop_width = backdrop_right - backdrop_left
            backdrop_height = backdrop_bottom - backdrop_top

            # Более нежная, почти невидимая подложка
            header_backdrop = pygame.Surface(
                (backdrop_width, backdrop_height),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                header_backdrop,
                (0, 0, 0, 130),  # мягкий полупрозрачный чёрный
                header_backdrop.get_rect(),
                border_radius=14,
            )

            screen.blit(header_backdrop, (backdrop_left, backdrop_top))

            # Теперь поверх — сам статус и цитата
            for surf, rect in header_items:
                screen.blit(surf, rect)

        # ============ Меню ============
        self.option_rects = []

        # геометрия меню: стартуем довольно близко к цитате, без гигантской дыры
        menu_spacing: int = 50
        menu_y = current_y + 60

        # анимация: ease-out для сдвига и прозрачности
        if self.menu_anim_duration_ms > 0:
            t = self.menu_anim_time_ms / self.menu_anim_duration_ms
            t = max(0.0, min(1.0, t))
            eased = t * (2.0 - t)  # ease-out
        else:
            eased = 1.0

        alpha = int(255 * eased)
        slide_offset = int((1.0 - eased) * 30)

        # сначала собираем все пункты меню: поверхности и их прямоугольники
        items: list[tuple[pygame.Surface, pygame.Rect]] = []

        for idx, label in enumerate(self.options):
            decorated = self._decorate_label(label)
            color = (255, 220, 120) if idx == self.selected_index else (220, 220, 220)

            item_y = menu_y + idx * menu_spacing + slide_offset

            surf = render_mixed_text(
                decorated,
                self.font_menu,
                self.emoji_menu,
                color,
            )

            if alpha < 255:
                surf = surf.copy()
                surf.set_alpha(alpha)

            rect = surf.get_rect(center=(width // 2, item_y))

            self.option_rects.append(rect)
            items.append((surf, rect))

        if items:
            # вычисляем общий прямоугольник под все пункты меню
            min_left = min(rect.left for _, rect in items)
            max_right = max(rect.right for _, rect in items)
            min_top = min(rect.top for _, rect in items)
            max_bottom = max(rect.bottom for _, rect in items)

            padding_x = 50
            padding_y = 30

            backdrop_left = max(0, min_left - padding_x)
            backdrop_top = max(0, min_top - padding_y)
            backdrop_right = min(width, max_right + padding_x)
            backdrop_bottom = min(height, max_bottom + padding_y)

            backdrop_width = backdrop_right - backdrop_left
            backdrop_height = backdrop_bottom - backdrop_top

            # полупрозрачная подложка под меню
            backdrop = pygame.Surface((backdrop_width, backdrop_height), pygame.SRCALPHA)
            backdrop.fill((0, 0, 0, 150))

            # лёгкая рамка
            pygame.draw.rect(
                backdrop,
                (255, 255, 255, 40),
                backdrop.get_rect(),
                width=2,
                border_radius=18,
            )

            screen.blit(backdrop, (backdrop_left, backdrop_top))

            # теперь рисуем сами пункты меню поверх подложки
            for surf, rect in items:
                screen.blit(surf, rect)

    # -------------------------------
    #   Helpers
    # -------------------------------

    def _activate_option(self) -> None:
        """Вызывает callback в зависимости от выбранного пункта меню."""
        label = self.options[self.selected_index]

        if label == "Начать игру":
            self.on_start_game()
        elif label == "Лидерборд":
            self.on_show_leaderboard()
        elif label == "Сменить игрока" and self.on_change_player is not None:
            self.on_change_player()
        elif label == "Режим игры" and self.on_change_mode is not None:
            self.on_change_mode()
        elif label == "Мультиплеер (очередь)" and self.on_setup_multiplayer is not None:
            self.on_setup_multiplayer()
        elif label == "Выход":
            self.on_exit()

    def _handle_mouse_motion(self, mouse_pos: tuple[int, int]) -> None:
        """Подсвечивает пункт меню при наведении курсора."""
        for idx, rect in enumerate(self.option_rects):
            if rect.collidepoint(mouse_pos):
                self.selected_index = idx
                break

    def _handle_mouse_click(self, mouse_pos: tuple[int, int]) -> None:
        """Активирует пункт меню по клику мышью."""
        for idx, rect in enumerate(self.option_rects):
            if rect.collidepoint(mouse_pos):
                self.selected_index = idx
                self._activate_option()
                break

    @staticmethod
    def _decorate_label(label: str) -> str:
        """Добавляет к пунктам меню небольшие emoji-иконки.

        Используем только те emoji, которые есть в EMOJI_CHARS в ui.py.
        """
        if label == "Начать игру":
            return "🎮 " + label
        if label == "Лидерборд":
            return "🏆 " + label
        if label == "Сменить игрока":
            return "🙂 " + label
        if label == "Режим игры":
            return "⚙ " + label
        if label == "Мультиплеер (очередь)":
            return "👥 " + label
        if label == "Выход":
            return "🚪 " + label
        return label

    def _load_background(self) -> None:
        """
        Загружает фоновое изображение меню, если оно доступно.

        Картинка ищется по пути:
            <корень проекта>/resources/images/menu_background.png
        относительно расположения этого файла (state_machine/main_menu.py).
        """
        project_root = os.path.dirname(os.path.dirname(__file__))
        bg_path = os.path.join(project_root, "resources", "images", "menu_background.png")

        try:
            background = pygame.image.load(bg_path).convert()
        except FileNotFoundError:
            self.background_image = None
            self.background_scaled = None
            self.background_scaled_size = None
            return

        self.background_image = background
        self.background_scaled = None
        self.background_scaled_size = None

    def _load_logo(self) -> None:
        """
        Загружает логотип для верхней части меню, если он есть.

        Ищется по пути:
            <корень проекта>/resources/images/menu_logo.png
        относительно расположения этого файла.
        """
        project_root = os.path.dirname(os.path.dirname(__file__))
        logo_path = os.path.join(
            project_root,
            "resources",
            "images",
            "menu_logo.png",
        )

        try:
            logo = pygame.image.load(logo_path).convert_alpha()
        except FileNotFoundError:
            self.logo_image = None
            self.logo_scaled = None
            self.logo_scaled_size = None
            return

        self.logo_image = logo
        self.logo_scaled = None
        self.logo_scaled_size = None

    def _render_logo(self, screen: pygame.Surface) -> int:
        """
        Рисует логотип (или текстовый заголовок, если логотипа нет).

        Возвращает y-координату нижней границы заголовка.
        """
        width, _ = screen.get_size()

        # Фолбэк: текстовый заголовок, если нет логотипа
        if self.logo_image is None:
            assert self.font_title is not None
            assert self.emoji_title is not None
            title_surface = render_mixed_text(
                "Maze Walker",
                self.font_title,
                self.emoji_title,
            )
            title_rect = title_surface.get_rect(center=(width // 2, 130))
            screen.blit(title_surface, title_rect)
            return title_rect.bottom

        # Есть логотип — масштабируем с сохранением пропорций, побольше и пониже
        max_width = int(width * 0.7)
        max_height = 200
        target_size = self._fit_size(
            self.logo_image.get_size(),
            (max_width, max_height),
        )

        if (
            self.logo_scaled is None
            or self.logo_scaled_size != target_size
        ):
            self.logo_scaled = pygame.transform.smoothscale(
                self.logo_image,
                target_size,
            )
            self.logo_scaled_size = target_size

        assert self.logo_scaled is not None
        # центрируем логотип чуть ниже — ближе к центру верхней части экрана
        logo_rect = self.logo_scaled.get_rect(center=(width // 2, 175))
        screen.blit(self.logo_scaled, logo_rect)
        return logo_rect.bottom


    def _render_background(self, screen: pygame.Surface) -> None:
        """
        Отрисовывает фоновое изображение (со скейлингом под окно)
        либо однотонную заливку, если текстура не найдена.
        """
        if self.background_image is None:
            screen.fill((30, 30, 30))
            return

        width, height = screen.get_size()
        target_size = (width, height)

        if (
            self.background_scaled is None
            or self.background_scaled_size != target_size
        ):
            self.background_scaled = pygame.transform.smoothscale(
                self.background_image,
                target_size,
            )
            self.background_scaled_size = target_size

        assert self.background_scaled is not None
        screen.blit(self.background_scaled, (0, 0))

    @staticmethod
    def _fit_size(
        source_size: tuple[int, int],
        max_size: tuple[int, int],
    ) -> tuple[int, int]:
        """
        Возвращает размер, пропорционально вписанный в max_size.

        Используется для аккуратного масштабирования логотипа.
        """
        src_w, src_h = source_size
        max_w, max_h = max_size

        if src_w == 0 or src_h == 0:
            return max_w, max_h

        scale = min(max_w / src_w, max_h / src_h)
        return int(src_w * scale), int(src_h * scale)

