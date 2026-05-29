from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import pygame


@dataclass
class SpriteSheet:
    """
    Спрайт-лист с поддержкой отступов.
    frame_size: (w, h) кадра.
    margin:   (mx, my) — отступ от края листа до первого кадра.
    spacing:  (sx, sy) — промежуток между кадрами.
    """
    image: pygame.Surface
    frame_size: Tuple[int, int]
    margin: Tuple[int, int] = (0, 0)
    spacing: Tuple[int, int] = (0, 0)

    @classmethod
    def from_file(
        cls,
        path: str,
        frame_size: Tuple[int, int],
        *,
        margin: Tuple[int, int] = (0, 0),
        spacing: Tuple[int, int] = (0, 0),
    ) -> "SpriteSheet":
        sheet = pygame.image.load(path)
        if pygame.get_init() and pygame.display.get_init():
            try:
                sheet = sheet.convert_alpha()
            except pygame.error:
                sheet = sheet.convert()
        return cls(sheet, frame_size, margin, spacing)

    def _grid_cols_rows(self) -> Tuple[int, int]:
        w, h = self.frame_size
        mx, my = self.margin
        sx, sy = self.spacing
        sheet_w, sheet_h = self.image.get_size()
        cols = max(1, (sheet_w - mx + sx) // (w + sx))
        rows = max(1, (sheet_h - my + sy) // (h + sy))
        return cols, rows

    def get_frame(self, index: int) -> pygame.Surface:
        """Возвращает кадр по индексу с учётом margin/spacing."""
        w, h = self.frame_size
        mx, my = self.margin
        sx, sy = self.spacing
        cols, _ = self._grid_cols_rows()
        col = index % cols
        row = index // cols
        x = mx + col * (w + sx)
        y = my + row * (h + sy)
        frame = self.image.subsurface((x, y, w, h))
        return frame.copy()


class AnimatedSprite:
    """Простая анимация по спрайт-листу."""
    def __init__(self, sheet: SpriteSheet, frame_count: int, fps: float = 8.0, loop: bool = True) -> None:
        self.sheet = sheet
        self.frame_count = frame_count
        self.fps = fps
        self.loop = loop
        self.start_time = pygame.time.get_ticks()

    def get_current_frame(self, now_ms: int | None = None) -> pygame.Surface:
        if now_ms is None:
            now_ms = pygame.time.get_ticks()
        elapsed = now_ms - self.start_time
        idx = int(elapsed * self.fps / 1000)
        idx = idx % self.frame_count if self.loop else min(idx, self.frame_count - 1)
        return self.sheet.get_frame(idx)

    def draw(self, screen: pygame.Surface, pos: Tuple[int, int], scale: float = 1.0) -> None:
        frame = self.get_current_frame()
        if scale != 1.0:
            w, h = frame.get_size()
            # для пиксель-арта — без сглаживания
            frame = pygame.transform.scale(frame, (int(w * scale), int(h * scale)))
        screen.blit(frame, pos)
