from __future__ import annotations

"""
state_base.py — базовые интерфейсы и менеджер состояний для Maze Game.

FSM (конечный автомат состояний) управляет экранами:
    Главное меню
    Игра
    Пауза
    Выбор игрока
    Лидерборд
    Настройки (в будущем)
"""

import pygame
from typing import Optional, Protocol


class BaseState(Protocol):
    """
    Базовый интерфейс для состояния игры.

    Состояние обязано уметь:
        - enter(): выполняется при первом входе в состояние;
        - handle_event(): обработать pygame-событие;
        - update(dt_ms): обновить логику;
        - render(screen): нарисовать себя;
        - exit(): вызывается при выходе из состояния.

    Никакой игровой логики вне состояний — всё живёт внутри них.
    """

    def enter(self) -> None: ...
    def exit(self) -> None: ...

    def handle_event(self, event: pygame.event.Event) -> None: ...
    def update(self, dt_ms: int) -> None: ...
    def render(self, screen: pygame.Surface) -> None: ...


class StateManager:
    """
    Менеджер состояний — переключает между экранами,
    хранит текущее состояние и передаёт ему события.
    """

    def __init__(self) -> None:
        self.current: Optional[BaseState] = None

    def change_state(self, new_state: BaseState) -> None:
        """
        Переключает текущее состояние на новое.

        Вызывает exit() у старого и enter() у нового.
        """
        if self.current is not None:
            self.current.exit()

        self.current = new_state
        self.current.enter()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.current is not None:
            self.current.handle_event(event)

    def update(self, dt_ms: int) -> None:
        if self.current is not None:
            self.current.update(dt_ms)

    def render(self, screen: pygame.Surface) -> None:
        if self.current is not None:
            self.current.render(screen)
