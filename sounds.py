"""Звуковая подсистема Maze Game (без внешних файлов).

Генерирует короткие звуки на лету (int16, mono, 22.05 kHz):
- coin: короткий «дзынь»;
- diamond: звонче и длиннее;
- win: короткая мини-фанфара;
- lose: глухой «бум».

Если инициализация аудио невозможна, класс работает в «тихом» режиме.
"""

from __future__ import annotations

from array import array as array_t
from dataclasses import dataclass
import math
from typing import Optional

import pygame


@dataclass
class _ToneSpec:
    freq_hz: float
    ms: int
    vol: float = 1.0


class SoundBank:
    """
    Универсальный проигрыватель звуков.

    Если в папке ./resources/ есть mp3-файлы:
        - get-coin.mp3
        - get-diamond.mp3
        - win.mp3
        - lose.mp3
    то используются они.
    Иначе — fallback на встроенные синтезированные сигналы.
    """

    def __init__(self, *, master_volume: float = 0.6) -> None:
        import os
        self.enabled: bool = False
        self.master: float = max(0.0, min(1.0, master_volume))
        self._sr: int = 22_050
        self._coin: Optional[pygame.mixer.Sound] = None
        self._diamond: Optional[pygame.mixer.Sound] = None
        self._win: Optional[pygame.mixer.Sound] = None
        self._lose: Optional[pygame.mixer.Sound] = None

        try:
            pygame.mixer.init(frequency=self._sr, size=-16, channels=2, buffer=512)
            self.enabled = True
        except pygame.error:
            self.enabled = False
            return

        # путь к ресурсам
        base = os.path.join(os.path.dirname(__file__), "resources")

        # попытка загрузить mp3
        def load_if_exists(name: str) -> Optional[pygame.mixer.Sound]:
            path = os.path.join(base, name)
            if os.path.exists(path):
                try:
                    return pygame.mixer.Sound(path)
                except pygame.error:
                    return None
            return None

        self._coin = load_if_exists("get-coin.mp3")
        self._diamond = load_if_exists("get-diamond.mp3")
        self._win = load_if_exists("win.mp3")
        self._lose = load_if_exists("lose.mp3")

        # если чего-то нет — делаем fallback
        if not self._coin:
            self._coin = self._make_tone([_ToneSpec(1800, 70, 0.9)], fade_ms=15)
        if not self._diamond:
            self._diamond = self._make_tone(
                [_ToneSpec(2000, 90, 0.9), _ToneSpec(2600, 90, 0.9)],
                gap_ms=15,
                fade_ms=18,
            )
        if not self._win:
            self._win = self._make_tone(
                [_ToneSpec(880, 110, 0.8),
                 _ToneSpec(1175, 110, 0.8),
                 _ToneSpec(1568, 140, 0.8)],
                gap_ms=20,
                fade_ms=20,
            )
        if not self._lose:
            self._lose = self._make_tone([_ToneSpec(140, 200, 0.7)], wave="sine", fade_ms=25)

        # громкость
        for s in (self._coin, self._diamond, self._win, self._lose):
            if s is not None:
                s.set_volume(self.master)

    # --- публичные методы ---

    def play_coin(self) -> None:
        if self.enabled and self._coin:
            self._coin.play()

    def play_diamond(self) -> None:
        if self.enabled and self._diamond:
            self._diamond.play()

    def play_win(self) -> None:
        if self.enabled and self._win:
            self._win.play()

    def play_lose(self) -> None:
        if self.enabled and self._lose:
            self._lose.play()


    # ---------- генерация ----------

    def _make_tone(
        self,
        parts: list[_ToneSpec],
        *,
        wave: str = "sine",
        gap_ms: int = 0,
        fade_ms: int = 8,
    ) -> pygame.mixer.Sound:
        """Собирает несколько тонов в один буфер с зазорами."""
        samples: array_t = array_t("h")
        for i, spec in enumerate(parts):
            tone = self._tone_buffer(spec.freq_hz, spec.ms, spec.vol, wave=wave, fade_ms=fade_ms)
            samples.extend(tone)
            if i + 1 < len(parts) and gap_ms > 0:
                samples.extend(self._silence(gap_ms))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _tone_buffer(
        self, freq_hz: float, ms: int, vol: float, *, wave: str = "sine", fade_ms: int = 8
    ) -> array_t:
        """Генерирует буфер одного тона с простым fade-in/out, int16 mono."""
        length = max(1, int(self._sr * ms / 1000))
        fade_len = max(1, int(self._sr * fade_ms / 1000))
        amp = int(32767 * max(0.0, min(1.0, vol)))

        buf = array_t("h", [0] * length)
        two_pi_f = 2.0 * math.pi * freq_hz

        for n in range(length):
            t = n / self._sr
            # волна
            if wave == "sine":
                value = math.sin(two_pi_f * t)
            elif wave == "triangle":
                # прибл. треугольник через арксинус синуса
                value = 2.0 / math.pi * math.asin(math.sin(two_pi_f * t))
            else:
                value = math.sin(two_pi_f * t)

            # огибающая
            env = 1.0
            if n < fade_len:
                env = n / fade_len
            elif length - n < fade_len:
                env = (length - n) / fade_len

            buf[n] = int(amp * env * value)

        return buf

    def _silence(self, ms: int) -> array_t:
        """Небольшой отрезок тишины."""
        return array_t("h", [0] * max(1, int(self._sr * ms / 1000)))
