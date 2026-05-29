"""
maze_game.py — генерация остовных деревьев (Wilson) и лабиринтов на решётке m×n.

Ключевые функции:
- wilson_grid(...): равномерно случайное остовное дерево на решётке.
- tree_to_maze(...): преобразует дерево в бинарную матрицу лабиринта.
- set_entrance_exit_and_check(...): ставит вход/выход и проверяет проходимость.
- draw_tree(...), draw_maze(...): отрисовка.

Заметки по дизайну:
- Без глобальных m/n; все размеры передаются явно (rows, cols).
- Рандом управляем через seed (воспроизводимость) или внешний rng.
- Без затенений имён; в сигнатурах осмысленные названия параметров.
"""

import random
from typing import Callable, List, Tuple, Optional

from coins import spawn_coins, CoinRarity, rarity_icon
from effects import Effects
from gameplay.formatting import format_time
from gameplay.hud_text import build_hud_text
from gameplay.maze_positions import inner_cell_from_border
from gameplay.result_text import (
    build_attempt_info,
    prepare_end_menu_summary,
)
from gameplay.scoring import compute_score, prepare_run_score
from highscores import (
    Highscore,
    load_highscore,
    default_path as highscore_path,
)
from presentation.hud_rendering import compose_hud_background
from presentation.enemy_sprites import load_enemy_sheets_by_type
from presentation.world_rendering import render_world
from sounds import SoundBank
from sprites import AnimatedSprite

from runtime.coin_collection import CoinCollectionStats, collect_coin_at
from runtime.block_timers import update_block_timers
from runtime.enemy_updates import update_enemies
from runtime.run_persistence import handle_run_persistence
from runtime.session_stats import SessionStats

from grid_utils import DIRS4, in_bounds
from enemies import (
    spawn_enemies,
    spawn_enemies_by_scheme,
    ENEMY_SCHEMES,
    EnemyType,
    build_safe_zone,
)
from blocks import spawn_blocks
from palette import make_palette
from ui import (
    get_emoji_font,
    get_text_font,
    render_mixed_text,
    draw_end_menu,
    wait_end_choice,
    draw_pause_menu,
    wait_pause_choice,
)
from maze_gen import (
    wilson_grid,
    tree_to_maze,
    set_entrance_exit_and_check,
)

from session_controller import GameSessionController, RoundMode

Coord = Tuple[int, int]

# Размер сетки лабиринта в «логических» ячейках Wilson-генератора
MAZE_GRID_ROWS: int = 20
MAZE_GRID_COLS: int = 20

# Размер одной клетки (в пикселях)
MAZE_CELL_PX: int = 24


def compute_window_size() -> tuple[int, int]:
    """
    Возвращает размер окна в пикселях под текущий размер лабиринта.

    Генератор Wilson строит лабиринт размерами (2 * rows + 1) × (2 * cols + 1)
    в клетках. Здесь rows/cols — логические размеры сетки генерации.
    """
    maze_rows: int = MAZE_GRID_ROWS * 2 + 1
    maze_cols: int = MAZE_GRID_COLS * 2 + 1
    width_px: int = maze_cols * MAZE_CELL_PX
    height_px: int = maze_rows * MAZE_CELL_PX
    return width_px, height_px

# --- Хелперы для врагов ---

def passable(maze: list[list[int]], row: int, col: int) -> bool:
    """Возвращает True, если клетка (row, col) внутри лабиринта и проходима (0)."""
    rows_count, cols_count = len(maze), len(maze[0])
    return in_bounds(row, col, rows_count, cols_count) and maze[row][col] == 0

def passable_neighbors(maze: list[list[int]], row: int, col: int) -> list[tuple[int, int]]:
    """Список направлений (drow, dcol), ведущих из (row, col) в проходимые клетки."""
    return [
        (drow, dcol)
        for (drow, dcol) in DIRS4
        if passable(maze, row + drow, col + dcol)
    ]

def local_enemy_density(next_position: Coord, enemy_positions: set[Coord]) -> int:
    """Считает число врагов в окрестности 3×3 вокруг next_position (включая центр)."""
    row, col = next_position
    count = 0
    for drow in (-1, 0, 1):
        for dcol in (-1, 0, 1):
            if (row + drow, col + dcol) in enemy_positions:
                count += 1
    return count

# ---конец хелперов для врагов



# --- Утилиты ---

def sample_coins_count(
    rng: random.Random,
    *,
    min_count: int = 10,
    max_count: int = 25,
    base_probability: float = 0.9,
    decay: float = 0.7,
) -> int:
    """
    Выбирает количество монет между min_count и max_count
    с убывающей вероятностью добавить ещё одну монету.

    Логика:
    - начинаем с min_count;
    - для каждого дополнительного слота проверяем rng.random() < p;
    - после каждого успешного добавления p *= decay.

    В результате:
    - 11-я монета почти всегда появляется;
    - чем дальше к 25, тем реже — хвост распределения очень тонкий.
    """
    count = min_count
    extra_slots = max(0, max_count - min_count)
    probability = base_probability

    for _ in range(extra_slots):
        if rng.random() < probability:
            count += 1
            probability *= decay
        else:
            break

    return count

def play_maze(
    maze: List[List[int]],
    *,
    cell_px: int = 20,
    entry: Tuple[str, int] = ("left", 0),
    exit_: Tuple[str, int] = ("right", 0),
    fps: int = 60,
    seed_palette: Optional[int] = None,
    cells_per_sec: float = 12.0,
    enemies_count: int = 20,
    enemy_cells_per_sec: float = 4.0,
    enemy_scheme_key: Optional[str] = None,
    rng_seed: Optional[int] = None,
    blocks_count: int = 6,
    block_lifetime_ms: int = 4000,
    block_pulse_ms: int = 1200,
    new_level_factory: Optional[Callable[[], List[List[int]]]] = None,
    coins_count: int = 10,
    session_controller: Optional[GameSessionController] = None,
) -> str:
    """
    Интерактивная «ходилка» с врагами и экраном победы/поражения.

    Удерживай стрелку/WASD — движение с заданной скоростью до стены.
    [Enter]/[Space]/[R] или клик по кнопке — рестарт после конца.

    Функция возвращает управляющий код для внешнего FSM:

        "restart"   — перезапустить забег на том же лабиринте;
        "new"       — начать забег на новом лабиринте (если есть фабрика);
        "quit"      — завершить игру целиком;
        "menu"      — выйти в главное меню приложения.

    Если передан session_controller, результаты забегов записываются
    в SQLite (runs + player_stats) для текущего игрока.
    """
    """
    Интерактивная «ходилка» с врагами и экраном победы/поражения.
    Удерживай стрелку/WASD — движение с заданной скоростью до стены.
    [Enter]/[Space]/[R] или клик по кнопке — рестарт после конца.

    Если передан session_controller, результаты забегов записываются
    в SQLite (runs + player_stats) для текущего игрока.
    """

    import pygame

    # Определяем, с кем играем: с контроллером или в одиночном режиме.
    if session_controller is not None:
        current_player_profile = session_controller.current_player()
        stats = session_controller.get_session_stats_for(current_player_profile.player_id)
        active_player_id: Optional[int] = current_player_profile.player_id
        active_player_name: Optional[str] = current_player_profile.name
    else:
        stats = SessionStats()
        active_player_id = None
        active_player_name = None

    sound = SoundBank()
    effects = Effects()
    highscore: Highscore = load_highscore(highscore_path())

    def run_once() -> str:
        """Один забег. Возвращает: "restart" | "new" | "quit"."""
        effects.reset()
        maze_rows, maze_cols = len(maze), len(maze[0])
        ent_border, ext_border, path_ok = set_entrance_exit_and_check(
            maze, entry=entry, exit_=exit_
        )
        if not path_ok:
            print("Warning: no pass-through detected (unexpected for tree-based maze)")

        player = inner_cell_from_border(ent_border, entry[0])
        goal = inner_cell_from_border(ext_border, exit_[0])

        # Используем уже существующее окно, если оно создано (FSM-режим).
        # Если окна ещё нет (запуск maze_game в одиночку) — создаём новое
        # подходящего размера.
        screen = pygame.display.get_surface()
        if screen is None:
            screen = pygame.display.set_mode((maze_cols * cell_px, maze_rows * cell_px))

        pygame.display.set_caption("Maze Walker")
        clock = pygame.time.Clock()

        enemy_sheets_by_type = load_enemy_sheets_by_type()


        hud_font_size = max(14, cell_px // 2)
        font_hud_text = get_text_font(hud_font_size)
        font_hud_emoji = get_emoji_font(hud_font_size)

        colors = make_palette(seed_palette)
        wall_rgb, path_rgb = colors["wall"], colors["path"]
        player_rgb, goal_rgb = colors["player"], colors["goal"]

        # старт хронометража
        start_ms = pygame.time.get_ticks()

        trail: set[Coord] = {player}

        def can_step(row: int, col: int) -> bool:
            return (
                    in_bounds(row, col, maze_rows, maze_cols)
                    and maze[row][col] == 0
                    and (row, col) not in blocked_set
            )

        step_interval_ms = max(1, int(1000 / max(1e-9, cells_per_sec)))
        enemy_interval_ms = max(1, int(1000 / max(1e-9, enemy_cells_per_sec)))

        next_step_at_ms = 0
        last_direction: Tuple[int, int] = (0, 0)

        key_to_direction = {
            pygame.K_LEFT: (0, -1),
            pygame.K_a: (0, -1),
            pygame.K_RIGHT: (0, +1),
            pygame.K_d: (0, +1),
            pygame.K_UP: (-1, 0),
            pygame.K_w: (-1, 0),
            pygame.K_DOWN: (+1, 0),
            pygame.K_s: (+1, 0),
        }

        rng = random.Random(rng_seed)

        # --- враги ---
        safe_steps_start = 10  # радиус безопасности от старта (в шагах по клеткам)
        safe_steps_goal = 3  # опционально — около выхода поменьше

        forbidden_static = {player, goal}
        # добавим безопасные зоны
        safe_start = build_safe_zone(maze, player, safe_steps_start)
        safe_goal = build_safe_zone(maze, goal, safe_steps_goal)
        forbidden_static |= safe_start | safe_goal

        # выбор схемы спавна: либо схема по ключу, либо старое поведение
        if enemy_scheme_key is not None:
            scheme = ENEMY_SCHEMES.get(enemy_scheme_key)
        else:
            scheme = None

        if scheme is None:
            enemies = spawn_enemies(
                maze,
                enemies_count,
                rng,
                forbidden_static,
            )
        else:
            enemies = spawn_enemies_by_scheme(
                maze,
                scheme,
                rng,
                forbidden_static,
            )

        # разнести старт ходов + дать «grace» задержку, чтобы игрок успел отойти
        grace_ms = 900
        base_now = pygame.time.get_ticks()
        total_enemies = max(1, len(enemies))
        for idx_enemy, enemy in enumerate(enemies):
            stagger = idx_enemy * (enemy_interval_ms // total_enemies)
            enemy.next_step_at = base_now + grace_ms + stagger

        # --- каждому врагу — спрайт по типу и своя фаза анимации ---
        enemy_anims: list[AnimatedSprite] = []
        for enemy in enemies:
            sheet = enemy_sheets_by_type.get(enemy.type, enemy_sheets_by_type[EnemyType.HUNTER])

            anim = AnimatedSprite(sheet, frame_count=8, fps=6)
            # немного сдвигаем старт, чтобы не было синхронной «жвачки»
            anim.start_time -= rng.randint(0, 900)
            enemy_anims.append(anim)

        # --- блокирующие перегородки ---
        base_now_ms = pygame.time.get_ticks()
        # нельзя спаунить на игроке/цели и на врагах/других блоках
        forbidden_dynamic = {player, goal, *(e.pos for e in enemies)}
        blocks = spawn_blocks(maze, blocks_count, rng, forbidden_dynamic)
        for block in blocks:
            block.expires_at = base_now_ms + block_lifetime_ms

        # множество «запрещённых» для шага клеток — будем обновлять каждый кадр
        blocked_set: set[Coord] = set()

        won = False
        lost = False
        running = True

        # монеты: не ставим на игрока/цель/врагов/блоки
        forbidden_for_coins = {
            player,
            goal,
            *(e.pos for e in enemies),
            *(blk.pos for blk in blocks),
        }

        coins_total = sample_coins_count(
            rng,
            min_count=coins_count,  # сейчас coins_count=10 → это минимальное число монет
            max_count=25,
        )

        coins = spawn_coins(
            maze,
            coins_total,
            rng,
            forbidden_for_coins,
            ensure_min={
                CoinRarity.DIAMOND: 1,   # минимум 1 алмаз
                CoinRarity.GOLD: 2,      # минимум 2 золота
                CoinRarity.SILVER: 3,    # минимум 3 серебра
                CoinRarity.BRONZE: 4,    # минимум 4 бронзы
            },
        )

        coin_stats = CoinCollectionStats()

        while running:
            now_ms = pygame.time.get_ticks()

            # ---- события ----
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return "quit"
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE and not (won or lost):
                        # --- Пауза ---
                        pause_start = pygame.time.get_ticks()

                        rect_resume, rect_restart, rect_menu = draw_pause_menu(
                            screen,
                            cell_px=cell_px,
                            palette=colors,
                        )
                        pygame.display.flip()
                        pause_choice = wait_pause_choice(
                            rect_resume,
                            rect_restart,
                            rect_menu,
                        )

                        pause_end = pygame.time.get_ticks()
                        delta = pause_end - pause_start

                        # сдвигаем таймеры, чтобы время паузы не считалось
                        start_ms += delta
                        next_step_at_ms += delta
                        for enemy in enemies:
                            enemy.next_step_at += delta
                        for block in blocks:
                            block.expires_at += delta

                        if pause_choice == "resume":
                            continue
                        if pause_choice == "restart":
                            return "restart"
                        if pause_choice == "menu":
                            return "menu"
                        if pause_choice == "quit":
                            return "quit"

                    if ev.key in key_to_direction and not (won or lost):
                        drow0, dcol0 = key_to_direction[ev.key]
                        next_row0, next_col0 = player[0] + drow0, player[1] + dcol0
                        if can_step(next_row0, next_col0):
                            player = (next_row0, next_col0)
                            trail.add(player)
                            collect_coin_at(
                                position=player,
                                current_ms=now_ms,
                                coins=coins,
                                stats=coin_stats,
                                sound=sound,
                                effects=effects,
                            )
                            if player == goal:
                                won = True
                                sound.play_win()
                        last_direction = (drow0, dcol0)
                        next_step_at_ms = now_ms + step_interval_ms
                elif ev.type == pygame.KEYUP:
                    if ev.key in key_to_direction:
                        pressed = pygame.key.get_pressed()
                        pressed_dirs: list[tuple[int, int]] = []
                        if pressed[pygame.K_LEFT] or pressed[pygame.K_a]:
                            pressed_dirs.append((0, -1))
                        if pressed[pygame.K_RIGHT] or pressed[pygame.K_d]:
                            pressed_dirs.append((0, +1))
                        if pressed[pygame.K_UP] or pressed[pygame.K_w]:
                            pressed_dirs.append((-1, 0))
                        if pressed[pygame.K_DOWN] or pressed[pygame.K_s]:
                            pressed_dirs.append((+1, 0))
                        last_direction = pressed_dirs[-1] if pressed_dirs else (0, 0)

            # ---- автодвижение игрока ----
            if not (won or lost) and last_direction != (0, 0) and now_ms >= next_step_at_ms:
                drow, dcol = last_direction
                next_row, next_col = player[0] + drow, player[1] + dcol
                if can_step(next_row, next_col):
                    player = (next_row, next_col)
                    trail.add(player)
                    collect_coin_at(
                        position=player,
                        current_ms=now_ms,
                        coins=coins,
                        stats=coin_stats,
                        sound=sound,
                        effects=effects,
                    )
                    if player == goal:
                        won = True
                        sound.play_win()
                next_step_at_ms = now_ms + step_interval_ms

            # ---- ход врагов ----
            if not (won or lost):
                update_enemies(
                    enemies=enemies,
                    maze=maze,
                    player_pos=player,
                    rng=rng,
                    blocked_set=blocked_set,
                    now_ms=now_ms,
                )

            # ---- апдейт блоков (переезд по таймеру) ----
            update_block_timers(
                blocks=blocks,
                blocked_set=blocked_set,
                player_pos=player,
                goal=goal,
                enemies=enemies,
                maze=maze,
                rng=rng,
                now_ms=now_ms,
                block_lifetime_ms=block_lifetime_ms,
            )

            # столкновения
            if not (won or lost):
                for enemy in enemies:
                    if enemy.pos == player:
                        lost = True
                        sound.play_lose()
                        break

            # ---- рендер мира ----
            render_world(
                screen=screen,
                maze=maze,
                maze_rows=maze_rows,
                maze_cols=maze_cols,
                cell_px=cell_px,
                wall_rgb=wall_rgb,
                path_rgb=path_rgb,
                goal_rgb=goal_rgb,
                player_rgb=player_rgb,
                blocks=blocks,
                block_pulse_ms=block_pulse_ms,
                coins=coins,
                goal=goal,
                trail=trail,
                enemies=enemies,
                enemy_anims=enemy_anims,
                player=player,
                effects=effects,
                now_ms=now_ms,
            )

            # HUD: имя игрока (если есть контроллер), монеты и текущее время
            elapsed_ms_live = now_ms - start_ms
            hud_text = build_hud_text(
                active_player_name=active_player_name,
                coins_collected=coin_stats.total_value,
                bronze_count=coin_stats.bronze_count,
                silver_count=coin_stats.silver_count,
                gold_count=coin_stats.gold_count,
                diamond_count=coin_stats.diamond_count,
                elapsed_ms_live=elapsed_ms_live,
            )

            # --- HUD с полупрозрачной подложкой ---
            hud_surf = render_mixed_text(
                hud_text,
                font_hud_text,
                font_hud_emoji,
            )

            hud_bg, pad_x, pad_y = compose_hud_background(
                hud_surf,
                pad_x=6,
                pad_y=4,
                bg_rgba=(0, 0, 0, 135),
                border_radius=6,
            )

            # Рисуем подложку и текст
            screen.blit(hud_bg, (6, 4))
            screen.blit(hud_surf, (6 + pad_x, 4 + pad_y))

            # HUD/оверлеи конца
            if won or lost:
                prepared_score = prepare_run_score(
                    start_ms=start_ms,
                    now_ms=now_ms,
                    coins_value_sum=coin_stats.total_value,
                    diamond_count=coin_stats.diamond_count,
                    won=won,
                )
                elapsed_ms = prepared_score.elapsed_ms
                time_str = format_time(elapsed_ms)

                score = compute_score(
                    prepared_score.coins_value_sum,
                    prepared_score.elapsed_ms,
                    won=prepared_score.won,
                    diamond_count=prepared_score.diamond_count,
                    params=prepared_score.params,
                )

                handle_run_persistence(
                    highscore=highscore,
                    highscore_json_path=highscore_path(),
                    stats=stats,
                    session_controller=session_controller,
                    active_player_id=active_player_id,
                    score=score,
                    elapsed_ms=elapsed_ms,
                    coins_value_sum=coin_stats.total_value,
                    won=won,
                    bronze_count=coin_stats.bronze_count,
                    silver_count=coin_stats.silver_count,
                    gold_count=coin_stats.gold_count,
                    diamond_count=coin_stats.diamond_count,
                )

                # 2) формируем строки
                attempt_info = build_attempt_info(
                    won=won,
                    time_str=time_str,
                    coins_value_sum=coin_stats.total_value,
                    score=score,
                )

                session_info = stats.summary_line()
                prepared_summary = prepare_end_menu_summary(
                    attempt_info=attempt_info,
                    session_info=session_info,
                    best_time_ms=highscore.best_time_ms,
                    best_score=highscore.best_score,
                    max_coins_value=highscore.max_coins_value,
                    bronze_max=highscore.bronze_max,
                    silver_max=highscore.silver_max,
                    gold_max=highscore.gold_max,
                    diamond_max=highscore.diamond_max,
                    bronze_count=coin_stats.bronze_count,
                    silver_count=coin_stats.silver_count,
                    gold_count=coin_stats.gold_count,
                    diamond_count=coin_stats.diamond_count,
                )

                title = "ПОБЕДА!" if won else "ПОЙМАЛИ!"
                rect_restart, rect_new = draw_end_menu(
                    screen,
                    title,
                    prepared_summary.subtitle,
                    cell_px=cell_px,
                    palette=colors,
                )

                pygame.display.flip()
                choice_ = wait_end_choice(rect_restart, rect_new)  # "restart" | "new" | "quit"
                return choice_

            pygame.display.flip()
            clock.tick(fps)

        # <— если по какой-то причине вышли из while без return
        return "quit"  # safety: закрываем все пути возврата

        # главный цикл: рестарт/новый уровень без выхода из процесса

    while True:
        choice = run_once()  # "restart" | "new" | "quit" | "menu"

        if choice in ("quit", "menu"):
            return choice

        # В мультиплеерных режимах (не SINGLE) play_maze делает один забег
        # и отдаёт решение ("restart"/"new") наружу во внешний FSM.
        is_multiplayer_mode = (
            session_controller is not None
            and session_controller.mode is not RoundMode.SINGLE
        )

        if is_multiplayer_mode:
            return choice

        # Одиночный режим: старое поведение — управляем рестартом и
        # генерацией нового уровня внутри play_maze.
        if choice == "new":
            if new_level_factory is not None:
                maze = new_level_factory()
            else:
                rows = (len(maze) - 1) // 2
                cols = (len(maze[0]) - 1) // 2
                tree_edges = wilson_grid(rows, cols, seed=None)
                maze = tree_to_maze(rows, cols, tree_edges, extra_openings=0, seed=None)
        # choice == "restart" → просто повторяем run_once() с тем же maze

