from __future__ import annotations

"""
game_app.py — главный запуск игры Maze Game на основе конечного автомата состояний (FSM).

Здесь:
    - инициализируется pygame
    - создаётся StateManager
    - задаются переходы из меню в игру, в лидерборд и обратно
    - запускается главный игровой цикл
"""

import os
import random
import sys

import pygame

from state_machine.state_base import StateManager
from state_machine.main_menu import MainMenuState
from state_machine.player_select_state import PlayerSelectState
from state_machine.leaderboard_state import LeaderboardState
from state_machine.mode_select_state import ModeSelectState
from state_machine.multiplayer_setup_state import MultiplayerSetupState

from session_controller import GameSessionController, RoundMode

from highscore_adapter import migrate_highscore_if_needed
from db_manager import init_db

import maze_game  # используем play_maze как подэкран игрового состояния


MAIN_MENU_QUOTES: list[str] = [
    # — Твои оригинальные, оставили как просил —
    "Сегодня отличный день, чтобы немного заблудиться.",
    "Каждый лабиринт — это просто очень странная прямая.",
    "Главное — не победа. Главное — не умереть через 5 секунд.",
    "Слайм боится тебя не меньше, чем ты его... Почти.",
    "Если видишь выход — не факт, что это не вход куда похуже.",

    # — Новые, ламповые, философские, забавные —
    "Любой тупик — это просто поворот, который лень было дорисовывать.",
    "Лабиринт не бесконечен…",
    "Иногда самый короткий путь — это самый скучный.",
    "Удача любит смелых. Лабиринт — нет.",
    "Если ты слышишь шаги за спиной, остановись и получай удовольствие.",
    "Выход близко. Очень близко. Ну… относительно.",
    "Стены тоже нервничают, когда ты пробегаешь мимо.",
    "Поворот не туда — классика жанра.",
    "Каждая монета стоит того, чтобы рискнуть жизнью. Наверное.",
    "Самая опасная ловушка — твоя самоуверенность.",
    "Не все блуждают без цели. Но ты — да.",
    "Слаймы эволюционируют. Ты — тоже, надеюсь.",
    "Лучший маршрут — тот, который ты найдёшь случайно.",
    "Никогда не недооценивай стену. Она тоже старается.",
    "Если тебе кажется, что всё слишком просто — подожди пару секунд.",
    "Ты не заблудился. Ты исследуешь. Очень тщательно...",
    "Опыт — это когда умираешь в тех же местах, но уже с достоинством.",
    "Даже если кажется, что всё плохо — хотя бы не надо платить за ремонт.",
    "Лабиринт всё помнит. Особенно твои ошибки.",
    "Страх — это просто показатель, что враги рядом.",
    "Там, где есть монета, обязательно есть опасность. Или две.",
    "Никто не знает, кто построил лабиринт. Но он явно был любитель тупиков.",
    "Терпение — твой лучший друг. Быстрота — твой главный враг.",
    "Каждый поворот — выбор. И каждый выбор — потенциальный провал.",
    "Даже если путь кажется простым, ты всё равно найдёшь как ошибиться.",
]

QUOTE_PASTEL_COLORS = [
    (255, 185, 185),  # пастельно-розовый
    (255, 200, 170),  # мягко-персиковый
    (255, 235, 150),  # светло-золотистый
    (255, 220, 200),  # кремовый апельсин

    (200, 230, 160),  # нежный салатовый
    (180, 240, 190),  # мятный
    (170, 220, 255),  # небесно-голубой
    (190, 230, 255),  # акварельный голубой

    (195, 175, 255),  # светлая пастельная сирень
    (220, 180, 255),  # лавандовый
    (240, 200, 255),  # очень мягкая фиалка

    (255, 190, 220),  # тёплый розово-пионовый
    (255, 175, 210),  # клубничный йогурт

    (240, 255, 190),  # пастельно-лаймовый
    (255, 245, 200),  # тёплый ванильный
]

# ================================
#   Инициализация окружения
# ================================

def init_environment() -> str:
    """
    Подготавливает базу данных и мигрирует highscore.json.
    Возвращает путь к maze_stats.db.
    """
    base_dir = os.path.dirname(__file__)
    db_path = os.path.join(base_dir, "maze_stats.db")

    init_db(db_path)
    migrate_highscore_if_needed(db_path, legacy_player_name="Игрок 1")

    return db_path

# --- конец инита окружения ---

def show_player_select(manager: StateManager, session: GameSessionController) -> None:
    """
    Переключает FSM в состояние выбора игрока.
    """
    state = PlayerSelectState(
        manager=manager,
        session=session,
        on_selected=lambda: manager.change_state(make_main_menu(manager, session)),
        on_cancel=lambda: manager.change_state(make_main_menu(manager, session)),
    )
    manager.change_state(state)

def show_player_select_for_next_round(manager: StateManager, session: GameSessionController) -> None:
    """
    Открывает экран выбора игрока после завершённого раунда.

    После выбора игрока сразу запускается новый уровень.
    Отмена (Esc) ведёт в главное меню.
    """
    def on_selected() -> None:
        GameplayWrapper(manager, session).start_level()

    state = PlayerSelectState(
        manager=manager,
        session=session,
        on_selected=on_selected,
        on_cancel=lambda: manager.change_state(make_main_menu(manager, session)),
    )
    manager.change_state(state)

def show_mode_select(manager: StateManager, session: GameSessionController) -> None:
    """
    Переключает FSM в состояние выбора режима игры.
    """
    state = ModeSelectState(
        manager=manager,
        session=session,
        on_exit_to_menu=lambda: manager.change_state(make_main_menu(manager, session)),
    )
    manager.change_state(state)

def show_multiplayer_setup(manager: StateManager, session: GameSessionController) -> None:
    """
    Переключает FSM в состояние настройки мультиплеерной партии.
    """
    state = MultiplayerSetupState(
        manager=manager,
        session=session,
        on_done=lambda: manager.change_state(make_main_menu(manager, session)),
        on_cancel=lambda: manager.change_state(make_main_menu(manager, session)),
    )
    manager.change_state(state)

def _format_round_mode_label(mode: RoundMode) -> str:
    """Человекочитаемое название режима для главного меню."""
    if mode == RoundMode.SINGLE:
        return "Одиночный"
    if mode == RoundMode.ROTATE_QUEUE:
        return "Очередь игроков"
    if mode == RoundMode.PICK_EACH_ROUND:
        return "Выбор перед раундом"
    return str(mode)


def build_main_menu_status(session: GameSessionController) -> str:
    """
    Формирует строку статуса вида:
    'Режим: Одиночный · Игрок: Irwyn'
    или для очереди:
    'Режим: Очередь игроков · Сейчас ходит: Irwyn'
    """
    mode_label = _format_round_mode_label(session.mode)
    player = session.current_player()
    player_name = player.name if player is not None else "—"

    if session.mode == RoundMode.ROTATE_QUEUE:
        return f"Режим: {mode_label} · Сейчас ходит: {player_name}"

    return f"Режим: {mode_label} · Игрок: {player_name}"

def make_main_menu(
    manager: StateManager,
    session: GameSessionController,
) -> MainMenuState:
    """
    Создаёт состояние главного меню.

    Здесь же формируем:
        - строку статуса (режим + текущий игрок);
        - случайную цитату для подписи под заголовком.
    """
    status_line = build_main_menu_status(session)
    quote_text = random.choice(MAIN_MENU_QUOTES)
    quote_color = random.choice(QUOTE_PASTEL_COLORS)

    return MainMenuState(
        manager,
        status_line=status_line,
        quote_text=quote_text,
        quote_color=quote_color,
        on_start_game=lambda: GameplayWrapper(manager, session).start_level(),
        on_show_leaderboard=lambda: show_leaderboard(manager, session),
        on_change_player=lambda: show_player_select(manager, session),
        on_change_mode=lambda: show_mode_select(manager, session),
        on_setup_multiplayer=lambda: show_multiplayer_setup(manager, session),
        on_exit=quit_game,
    )


# ================================
#   Состояние игры (адаптер)
# ================================

class GameplayWrapper:
    """
    Вспомогательный класс, который запускает play_maze() как состояние.

    Здесь мы НЕ создаём отдельный State-класс —
    play_maze уже содержит цикл до конца забега.

    Поэтому GameplayWrapper просто вызывает play_maze,
    а затем возвращает управление обратно в FSM.
    """

    def __init__(self, manager: StateManager, session: GameSessionController) -> None:
        self.manager = manager
        self.session = session

    def start_level(self) -> None:
        """
        Запускает один уровень Maze Game.

        После завершения забега анализирует код возврата play_maze и
        принимает решение, что делать дальше в зависимости от RoundMode:

        - SINGLE:
            play_maze сам обрабатывает рестарты/новые уровни и возвращает
            только "menu" или "quit"; здесь просто выходим в меню или закрываем игру.

        - ROTATE_QUEUE:
            после каждого завершённого забега вызываем advance_after_run()
            и сразу запускаем следующий уровень за следующим игроком.

        - PICK_EACH_ROUND:
            после каждого завершённого забега вызываем advance_after_run()
            и открываем экран выбора игрока; после выбора стартует новый уровень.
        """
        rows: int = maze_game.MAZE_GRID_ROWS
        cols: int = maze_game.MAZE_GRID_COLS

        def build_maze() -> list[list[int]]:
            """Строит лабиринт с теми же параметрами, что и текущий старт уровня."""
            tree_edges = maze_game.wilson_grid(rows, cols, seed=None)
            return maze_game.tree_to_maze(
                rows,
                cols,
                tree_edges,
                extra_openings=40,
                seed=123,
            )

        while True:
            maze = build_maze()

            def new_level() -> list[list[int]]:
                """
                Фабрика нового уровня для одиночного режима.

                Использует те же размеры сетки и параметры генерации,
                что и стартовый уровень.
                """
                return build_maze()

            choice = maze_game.play_maze(
                maze,
                cell_px=maze_game.MAZE_CELL_PX,
                entry=("left", 0),
                exit_=("right", cols - 1),
                seed_palette=None,
                blocks_count=12,
                block_lifetime_ms=4000,
                block_pulse_ms=1200,
                new_level_factory=new_level,
                enemy_scheme_key="D_MIXED",
                session_controller=self.session,
            )

            # Если пользователь попросил полностью выйти — выходим сразу.
            if choice == "quit":
                quit_game()

            # Если вернулись в меню — просто переключаемся на главное меню.
            if choice == "menu":
                self.manager.change_state(make_main_menu(self.manager, self.session))
                return

            # На этом этапе остались только варианты "restart" / "new".
            # Считаем, что забег завершён и можно обновить режим/очередь игроков.
            self.session.advance_after_run()

            # Режим выбора игрока перед КАЖДЫМ раундом:
            # после забега открываем экран выбора игрока, а он уже запускает
            # новый уровень через GameplayWrapper(...).start_level().
            if self.session.mode == RoundMode.PICK_EACH_ROUND:
                show_player_select_for_next_round(self.manager, self.session)
                return

            # Одиночный режим и режим очереди:
            # просто стартуем следующий уровень автоматически.
            if self.session.mode in (RoundMode.SINGLE, RoundMode.ROTATE_QUEUE):
                continue

            # Защитный fallback: если окажется неизвестный режим — вернёмся в меню.
            self.manager.change_state(make_main_menu(self.manager, self.session))
            return




# ================================
#   Лидерборд (пока прототип)
# ================================

def show_leaderboard(manager: StateManager, session: GameSessionController) -> None:
    """
    Переключает FSM в состояние лидерборда.
    """
    state = LeaderboardState(
        manager=manager,
        session=session,
        on_exit_to_menu=lambda: manager.change_state(make_main_menu(manager, session)),
    )
    manager.change_state(state)


# ================================
#   Выход
# ================================

def quit_game() -> None:
    """Аккуратно завершает pygame и процесс."""
    pygame.quit()
    sys.exit(0)


# ================================
#   Главный запуск
# ================================

def run_game_app() -> None:
    """
    Точка входа в игру.

    Создаёт окно нужного размера под лабиринт и запускает FSM-цикл.
    """
    pygame.init()

    window_size: tuple[int, int] = maze_game.compute_window_size()
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption("Maze Game — FSM Edition")

    clock = pygame.time.Clock()

    db_path = init_environment()
    session = GameSessionController.from_db(db_path, mode=RoundMode.SINGLE)

    manager = StateManager()

    # создаём главное меню
    main_menu = make_main_menu(manager, session)
    manager.change_state(main_menu)

    # главный цикл pygame + FSM
    while True:
        dt = clock.tick(60)  # миллисекунды между кадрами

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            manager.handle_event(event)

        manager.update(dt)
        manager.render(screen)

        pygame.display.flip()



# ================================
#   Точка входа
# ================================

if __name__ == "__main__":
    run_game_app()
