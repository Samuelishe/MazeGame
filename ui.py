"""UI helpers for Maze Game: emoji-capable fonts and end-screen."""

from __future__ import annotations

import os

import pygame

EMOJI_CHARS: set[str] = {
    "💰",
    "🥉",
    "🥈",
    "🥇",
    "💎",
    "⏱",
    "🎮",
    "🏆",
    "🙂",
    "⚙",
    "👥",
    "🚪",
    "👤",
    "🎲",
    "🟦",
    "⬛",
    "➡",
    "⭐",
    "🟢",  # места 6–15
    "🟡",  # места 16–25
    "🟠",  # места 26–35
    "🔴",  # места 36–45
}

def get_emoji_font(size: int) -> "pygame.font.Font":
    """
    Возвращает шрифт с поддержкой эмодзи (если найдётся), иначе SysFont.
    Windows: Segoe UI Emoji
    macOS:   Apple Color Emoji
    Linux:   Noto Color Emoji
    """
    candidates = [
        "C:/Windows/Fonts/seguiemj.ttf",                          # Windows
        "/System/Library/Fonts/Apple Color Emoji.ttc",            # macOS
        "/usr/share/fonts/noto/NotoColorEmoji.ttf",               # Linux (варианты путей)
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/emoji/NotoColorEmoji.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except (FileNotFoundError, OSError, pygame.error):
                continue

    for name in ("Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", "Twitter Color Emoji"):
        matched = pygame.font.match_font(name)
        if matched:
            try:
                return pygame.font.Font(matched, size)
            except (FileNotFoundError, OSError, pygame.error):
                continue

    return pygame.font.SysFont("consolas", size, bold=True)


def _get_text_font(size: int) -> "pygame.font.Font":
    """Базовый латиница/кириллица шрифт для HUD/меню."""
    for name in ("Segoe UI", "Arial", "DejaVu Sans", "Liberation Sans"):
        matched = pygame.font.match_font(name)
        if matched:
            try:
                return pygame.font.Font(matched, size)
            except (FileNotFoundError, OSError, pygame.error):
                continue
    return pygame.font.SysFont("consolas", size, bold=True)

def get_text_font(size: int) -> "pygame.font.Font":
    """
    Возвращает базовый шрифт для текста (латиница + кириллица).

    Это публичная обёртка над _get_text_font, чтобы HUD и
    другие части игры могли использовать один и тот же
    текстовый шрифт.
    """
    return _get_text_font(size)

def render_mixed_text(
    text: str,
    font_text: "pygame.font.Font",
    font_emoji: "pygame.font.Font",
    color: tuple[int, int, int] = (255, 255, 255),
) -> "pygame.Surface":
    """
    Рендерит строку текста, смешивая обычный текстовый шрифт и emoji-шрифт.

    Все символы из EMOJI_CHARS рисуются font_emoji, остальные — font_text.
    Это позволяет одновременно отображать кириллицу и эмодзи.
    """
    pieces: list["pygame.Surface"] = []
    total_w = 0
    max_h = 0
    buffer = ""

    def flush_buffer() -> None:
        nonlocal buffer, total_w, max_h
        if not buffer:
            return
        surf_ = font_text.render(buffer, True, color)
        pieces.append(surf_)
        total_w += surf_.get_width()
        max_h = max(max_h, surf_.get_height())
        buffer = ""

    for ch in text:
        if ch in EMOJI_CHARS:
            flush_buffer()
            try:
                surf = font_emoji.render(ch, True, color)
                # некоторых «эмодзи» шрифт может не уметь; подстрахуемся
                if surf.get_width() == 0:
                    raise pygame.error("zero-width glyph")
            except pygame.error:
                # если эмодзи не получилось — рендерим как обычный текст,
                # чтобы не падать
                surf = font_text.render(ch, True, color)

            pieces.append(surf)
            total_w += surf.get_width()
            max_h = max(max_h, surf.get_height())
        else:
            buffer += ch
    flush_buffer()

    if not pieces:
        return font_text.render("", True, color)

    surface = pygame.Surface((total_w, max_h), pygame.SRCALPHA)
    x = 0
    for surf in pieces:
        surface.blit(surf, (x, (max_h - surf.get_height()) // 2))
        x += surf.get_width()
    return surface

def draw_end_menu(
    screen: "pygame.Surface",
    title: str,
    subtitle: str,
    *,
    cell_px: int,
    palette: dict[str, tuple[int, int, int]],
) -> tuple["pygame.Rect", "pygame.Rect"]:
    """
    Рисует затемнённый оверлей с результатом и кнопками.
    Возвращает прямоугольники кнопок (restart, new).
    """
    width, height = screen.get_size()

    # затемнение
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    font_title_text = _get_text_font(max(24, cell_px))
    font_sub_text = _get_text_font(max(16, cell_px // 2))
    font_btn_text = _get_text_font(max(18, cell_px // 2))
    font_emoji = get_emoji_font(max(16, cell_px // 2))
    font_emoji_big = get_emoji_font(max(24, cell_px))

    emoji_set = {"🥉", "🥈", "🥇", "💎", "⏱", "💰"}

    def render_mixed(line: str, text_font: "pygame.font.Font",
                     emoji_font: "pygame.font.Font",
                     color=(230, 230, 230)) -> "pygame.Surface":
        pieces: list[pygame.Surface] = []
        total_w, h = 0, 0
        buf = ""

        def flush_buf() -> None:
            nonlocal total_w, h, buf
            if not buf:
                return
            s_text = text_font.render(buf, True, color)
            pieces.append(s_text)
            total_w += s_text.get_width()
            h = max(h, s_text.get_height())
            buf = ""

        for ch in line:
            if ch in emoji_set:
                flush_buf()
                s_emoji = emoji_font.render(ch, True, color)
                pieces.append(s_emoji)
                total_w += s_emoji.get_width()
                h = max(h, s_emoji.get_height())
            else:
                buf += ch
        flush_buf()

        if not pieces:
            return text_font.render("", True, color)

        merged = pygame.Surface((total_w, h), pygame.SRCALPHA)
        x = 0
        for surf in pieces:
            merged.blit(surf, (x, (h - surf.get_height()) // 2))
            x += surf.get_width()
        return merged

    title_surf = render_mixed(title, font_title_text, font_emoji_big, (255, 255, 255))
    title_h = title_surf.get_height()

    lines = subtitle.splitlines()
    sub_surfs = [render_mixed(line, font_sub_text, font_emoji) for line in lines]
    line_gap = 4
    sub_lines_h = sum(s.get_height() for s in sub_surfs) + max(0, len(sub_surfs) - 1) * line_gap
    sub_max_w = max((s.get_width() for s in sub_surfs), default=0)
    pad_x, pad_y = 12, 6
    card_w = sub_max_w + pad_x * 2
    card_h = sub_lines_h + pad_y * 2

    labels = ["Начать сначала", "Другой уровень"]
    btn_surfs = [font_btn_text.render(lbl, True, (0, 0, 0)) for lbl in labels]
    padd_w, padd_h = cell_px * 2, cell_px
    btn_sizes = [
        (max(s.get_width() + padd_w, cell_px * 8), max(s.get_height() + padd_h, cell_px * 2))
        for s in btn_surfs
    ]
    btn_h = max(h for _, h in btn_sizes)
    gap_title_to_card = max(cell_px // 2, 10)
    gap_card_to_btns = max(cell_px, 14)
    gap_between_btns = cell_px

    total_pack_h = title_h + gap_title_to_card + card_h + gap_card_to_btns + btn_h
    top = (height - total_pack_h) // 2

    # Title
    title_rect = title_surf.get_rect(center=(width // 2, top + title_h // 2))
    screen.blit(title_surf, title_rect)

    # Subtitle card
    card_top = title_rect.bottom + gap_title_to_card
    card_rect = pygame.Rect((width - card_w) // 2, card_top, card_w, card_h)
    pygame.draw.rect(screen, (0, 0, 0, 160), card_rect, border_radius=10)
    pygame.draw.rect(screen, palette["wall"], card_rect, width=2, border_radius=10)

    y_cursor = card_top + pad_y
    for s in sub_surfs:
        s_rect = s.get_rect(center=(width // 2, y_cursor + s.get_height() // 2))
        screen.blit(s, s_rect)
        y_cursor += s.get_height() + line_gap

    # Buttons
    btn_top = card_rect.bottom + gap_card_to_btns
    total_btn_w = btn_sizes[0][0] + btn_sizes[1][0] + gap_between_btns
    left_x = (width - total_btn_w) // 2

    rect_restart = pygame.Rect(left_x, btn_top, *btn_sizes[0])
    rect_new = pygame.Rect(rect_restart.right + gap_between_btns, btn_top, *btn_sizes[1])

    wall_rgb = palette["wall"]
    for rect in (rect_restart, rect_new):
        pygame.draw.rect(screen, (245, 245, 245), rect, border_radius=10)
        pygame.draw.rect(screen, wall_rgb, rect, width=3, border_radius=10)

    screen.blit(btn_surfs[0], btn_surfs[0].get_rect(center=rect_restart.center))
    screen.blit(btn_surfs[1], btn_surfs[1].get_rect(center=rect_new.center))

    return rect_restart, rect_new


def wait_end_choice(rect_restart: "pygame.Rect", rect_new: "pygame.Rect") -> str:
    """
    Ожидает выбор игрока на экране конца.
    Возвращает: "restart" | "new" | "quit".
    """
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return "quit"
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                    return "restart"
                if ev.key == pygame.K_n:
                    return "new"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if rect_restart.collidepoint(ev.pos):
                    return "restart"
                if rect_new.collidepoint(ev.pos):
                    return "new"
        pygame.time.delay(10)

def draw_pause_menu(
    screen: "pygame.Surface",
    *,
    cell_px: int,
    palette: dict[str, tuple[int, int, int]],
) -> tuple["pygame.Rect", "pygame.Rect", "pygame.Rect"]:
    """
    Рисует оверлей паузы поверх текущего экрана.

    Возвращает кортеж прямоугольников кнопок:
        (rect_resume, rect_restart, rect_menu)
    """
    width, height = screen.get_size()

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    font_title = _get_text_font(max(28, cell_px))
    font_btn = _get_text_font(max(18, cell_px // 2))

    title_surf = font_title.render("Пауза", True, (255, 255, 255))
    title_rect = title_surf.get_rect(center=(width // 2, height // 2 - cell_px * 2))
    screen.blit(title_surf, title_rect)

    labels = ["Продолжить", "Заново", "В меню"]
    btn_surfs = [font_btn.render(text, True, (0, 0, 0)) for text in labels]

    pad_x = cell_px * 2
    pad_y = cell_px // 2

    btn_sizes = [
        (max(s.get_width() + pad_x, cell_px * 6),
         max(s.get_height() + pad_y, cell_px * 2))
        for s in btn_surfs
    ]
    total_width = btn_sizes[0][0] + btn_sizes[1][0] + btn_sizes[2][0] + cell_px * 2
    top = title_rect.bottom + cell_px

    x = (width - total_width) // 2

    rects: list[pygame.Rect] = []
    wall_rgb = palette["wall"]

    for size, surf in zip(btn_sizes, btn_surfs):
        rect = pygame.Rect(x, top, *size)
        pygame.draw.rect(screen, (245, 245, 245), rect, border_radius=10)
        pygame.draw.rect(screen, wall_rgb, rect, width=3, border_radius=10)

        surf_rect = surf.get_rect(center=rect.center)
        screen.blit(surf, surf_rect)

        rects.append(rect)
        x += size[0] + cell_px

    rect_resume, rect_restart, rect_menu = rects
    return rect_resume, rect_restart, rect_menu


def wait_pause_choice(
    rect_resume: "pygame.Rect",
    rect_restart: "pygame.Rect",
    rect_menu: "pygame.Rect",
) -> str:
    """
    Ожидает выбор на экране паузы.

    Возвращает:
        "resume"  — продолжить игру;
        "restart" — начать забег заново;
        "menu"    — выйти в главное меню;
        "quit"    — закрыть игру (закрытие окна).
    """
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_p):
                    return "resume"
                if ev.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                    return "restart"
                if ev.key in (pygame.K_m, pygame.K_BACKSPACE):
                    return "menu"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if rect_resume.collidepoint(ev.pos):
                    return "resume"
                if rect_restart.collidepoint(ev.pos):
                    return "restart"
                if rect_menu.collidepoint(ev.pos):
                    return "menu"

        pygame.time.delay(10)