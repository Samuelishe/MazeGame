"""Enemy logic for Maze Game: spawn, movement choice, safe zones."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Optional

import random

from grid_utils import DIRS4, in_bounds

Coord = tuple[int, int]


class EnemyType(Enum):
    """
    Тип врага в лабиринте.

    SLIME:
        Базовый глупый враг (как текущие слаймы).
    MEDIUM:
        Более быстрый, но всё ещё «тупой» враг (рандомное движение).
    HUNTER:
        Охотник, который в будущем будет тянуться к игроку.
    PATROLLER:
        Патрульный враг, в будущем будет ходить по маршруту.
    """

    SLIME = auto()
    MEDIUM = auto()
    HUNTER = auto()
    PATROLLER = auto()


@dataclass(frozen=True)
class EnemyParams:
    """
    Параметры типа врага.

    speed_cells_per_sec:
        Скорость движения по сетке (клеток в секунду).
    aggro_radius:
        Радиус «агрессии» для умных врагов (HUNTER и т.п.), в клетках.
        Для простых врагов (SLIME, MEDIUM, PATROLLER) можно оставлять 0.
    """

    speed_cells_per_sec: float
    aggro_radius: int = 0


#: Базовый конфиг типов врагов.
ENEMY_PARAMS: dict[EnemyType, EnemyParams] = {
    # зелёные: самые медленные, фоновый мусор
    EnemyType.SLIME: EnemyParams(speed_cells_per_sec=2.0, aggro_radius=0),
    # жёлтые: середнячки
    EnemyType.MEDIUM: EnemyParams(speed_cells_per_sec=5.0, aggro_radius=0),
    # красные (хантер): самые быстрые и умные
    # скорость близка к прежним жёлтым (5.0), но немного мягче
    EnemyType.HUNTER: EnemyParams(speed_cells_per_sec=4.0, aggro_radius=8),
    # патрульный — на уровне средних (пока логика — как у MEDIUM)
    EnemyType.PATROLLER: EnemyParams(speed_cells_per_sec=5.5, aggro_radius=0),
}


def step_interval_ms_for(enemy_type: EnemyType) -> int:
    """
    Возвращает интервал между шагами врага данного типа в миллисекундах.

    Интервал вычисляется как 1000 / speed_cells_per_sec с защитой от деления
    на ноль.
    """
    params = ENEMY_PARAMS[enemy_type]
    speed = max(1e-9, params.speed_cells_per_sec)
    return max(1, int(1000 / speed))


EnemyScheme = dict[EnemyType, int]
"""
Схема спавна врагов: сколько врагов каждого типа создать.

Пример:
    {EnemyType.SLIME: 8, EnemyType.MEDIUM: 3}
означает: 8 слаймов и 3 средних врага.
"""


#: Набор предопределённых схем спавна.
#: Используются как пресеты сложности и структуры волны.
ENEMY_SCHEMES: dict[str, EnemyScheme] = {
    # Мягкий старт: только медленные слаймы.
    "A_EASY": {
        EnemyType.SLIME: 8,
    },
    # Чуть плотнее: немного более быстрых врагов.
    "B_MEDIUM": {
        EnemyType.SLIME: 10,
        EnemyType.MEDIUM: 3,
    },
    # Охотник + свита.
    "C_HUNTER": {
        EnemyType.SLIME: 8,
        EnemyType.MEDIUM: 4,
        EnemyType.HUNTER: 1,
    },
    # Смешанная группа для более жёстких забегов.
    "D_MIXED": {
        EnemyType.SLIME: 8,
        EnemyType.MEDIUM: 4,
        EnemyType.HUNTER: 2,
        EnemyType.PATROLLER: 2,
    },
}

@dataclass
class Enemy:
    """
    Сущность врага на сетке.

    pos:
        Текущая клетка (row, col).
    direction:
        Текущее направление шага (drow, dcol).
    next_step_at:
        Время (ms), когда враг может сделать следующий шаг.
    type:
        Логический тип врага (SLIME / MEDIUM / HUNTER / PATROLLER).
    step_interval_ms:
        Интервал между шагами для конкретного врага (зависит от type).
    move_strategy:
        Функция-стратегия, определяющая направление шага врага.
    last_pos:
        Предыдущая клетка (для будущих эвристик и анализа движения).
    oscillation:
        Фаза/счётчик «колебаний» (оставлен для совместимости;
        сейчас почти не используется).
    """

    pos: Coord
    direction: tuple[int, int]
    next_step_at: int
    type: EnemyType
    step_interval_ms: int
    move_strategy: "MoveStrategy"
    last_pos: Optional[Coord] = None
    oscillation: int = 0

    # поля для патрульных врагов
    patrol_path: Optional[list[Coord]] = None
    patrol_index: int = 0
    patrol_direction: int = 1


MoveStrategy = Callable[
    [list[list[int]], Enemy, Coord, random.Random, set[Coord]],
    tuple[int, int],
]
"""
Тип стратегии движения врага.

Параметры:
    maze:
        Матрица лабиринта (0 — путь, 1 — стена).
    enemy:
        Конкретный враг.
    player_pos:
        Текущая позиция игрока (row, col).
    rng:
        Генератор случайных чисел.
    blocked:
        Множество временно запрещённых клеток (например, блоки).

Возвращает:
    (drow, dcol) — сдвиг по строке и столбцу. (0, 0) означает «стоять».
"""


def _pick_free_cells(
    maze: list[list[int]],
    total_count: int,
    rng: random.Random,
    forbidden: set[Coord],
) -> list[Coord]:
    """
    Возвращает список свободных клеток для спавна, перемешанных случайно.

    :param maze:
        Матрица лабиринта, где 0 — путь, 1 — стена.
    :param total_count:
        Сколько позиций нужно выбрать (если свободных меньше —
        вернётся меньше).
    :param rng:
        Генератор случайных чисел.
    :param forbidden:
        Множество координат, куда спавнить нельзя.
    """
    rows_count, cols_count = len(maze), len(maze[0])
    free_cells: list[Coord] = [
        (r, c)
        for r in range(rows_count)
        for c in range(cols_count)
        if maze[r][c] == 0 and (r, c) not in forbidden
    ]
    rng.shuffle(free_cells)
    return free_cells[: max(0, total_count)]


def spawn_enemies_by_scheme(
    maze: list[list[int]],
    scheme: EnemyScheme,
    rng: random.Random,
    forbidden: set[Coord],
) -> list[Enemy]:
    """
    Размещает врагов по заданной схеме типов.

    :param maze:
        Матрица лабиринта (0 — путь, 1 — стена).
    :param scheme:
        Словарь {EnemyType: количество}, определяющий состав волны.
        Нулевые и отрицательные значения игнорируются.
    :param rng:
        Генератор случайных чисел.
    :param forbidden:
        Множество координат, куда ставить врагов нельзя.
    :return:
        Список Enemy с позициями, типами и таймингами шагов.
    """
    # Собираем список типов с повторениями.
    enemy_types: list[EnemyType] = []
    for enemy_type, count in scheme.items():
        if count <= 0:
            continue
        enemy_types.extend([enemy_type] * count)

    if not enemy_types:
        return []

    total = len(enemy_types)
    positions = _pick_free_cells(maze, total, rng, forbidden)
    if not positions:
        return []

    # Если свободных клеток меньше, чем типов — усечём список типов,
    # чтобы длины совпали.
    if len(positions) < len(enemy_types):
        enemy_types = enemy_types[: len(positions)]

    rng.shuffle(enemy_types)

    enemies: list[Enemy] = []
    for pos, enemy_type in zip(positions, enemy_types):
        interval_ms = step_interval_ms_for(enemy_type)
        strategy = MOVE_STRATEGIES[enemy_type]
        enemy = Enemy(
            pos=pos,
            direction=(0, 0),
            next_step_at=0,
            type=enemy_type,
            step_interval_ms=interval_ms,
            move_strategy=strategy,
        )

        if enemy_type is EnemyType.PATROLLER:
            enemy.patrol_path = build_patrol_path(
                maze,
                start=pos,
                rng=rng,
                min_length=10,
                max_length=20,
            )
            enemy.patrol_index = 0
            enemy.patrol_direction = 1

        enemies.append(enemy)

    return enemies


def spawn_enemies(
    maze: list[list[int]],
    count: int,
    rng: random.Random,
    forbidden: set[Coord],
) -> list[Enemy]:
    """
    Размещает врагов на свободных клетках (0), избегая forbidden.

    Обёртка над spawn_enemies_by_scheme, которая создаёт схему вида
    «только SLIME в количестве count». Используется для совместимости
    с существующим кодом.

    :param maze:
        Двумерный список (матрица лабиринта), где 0 — путь, 1 — стена.
    :param count:
        Сколько врагов нужно создать.
    :param rng:
        Генератор случайных чисел (для воспроизводимости).
    :param forbidden:
        Множество координат, куда ставить врагов нельзя
        (игрок, цель, безопасные зоны и т.п.).
    :return:
        Список Enemy с позицией, типом и таймингами шагов.
    """
    scheme: EnemyScheme = {EnemyType.SLIME: max(0, count)}
    return spawn_enemies_by_scheme(maze, scheme, rng, forbidden)


def choose_enemy_direction(
    maze: list[list[int]],
    row: int,
    col: int,
    current: tuple[int, int],
    rng: random.Random,
    *,
    blocked: set[Coord],
) -> tuple[int, int]:
    """
    Выбор направления для врага (случайное блуждание).

    Логика:
      - В «трубе» (ровно один вариант без разворота) — держим текущее
        направление.
      - На развилке (>= 2 вариантов без разворота) — случайный выбор
        (избегаем разворота).
      - В тупике — разворот (или единственный доступный).
      - Границы/стены/временные блоки учитываются через параметр blocked.
    """
    rows_count, cols_count = len(maze), len(maze[0])

    def can(cell: Coord) -> bool:
        r, c = cell
        return (
            in_bounds(r, c, rows_count, cols_count)
            and maze[r][c] == 0
            and cell not in blocked
        )

    neighbors: list[tuple[int, int]] = []
    for drow, dcol in DIRS4:
        nr, nc = row + drow, col + dcol
        if can((nr, nc)):
            neighbors.append((drow, dcol))

    if not neighbors:
        return 0, 0

    reverse = (-current[0], -current[1])
    forward_ok = current != (0, 0) and can((row + current[0], col + current[1]))

    options_no_back = [d for d in neighbors if d != reverse]
    if not options_no_back:
        return reverse if reverse in neighbors else neighbors[0]

    if forward_ok and len(options_no_back) == 1:
        return current

    return rng.choice(options_no_back)

def build_patrol_path(
    maze: list[list[int]],
    start: Coord,
    rng: random.Random,
    min_length: int = 12,
    max_length: int = 20,
) -> list[Coord]:
    """
    Строит маршрут для патрульного врага в виде последовательности клеток.

    Алгоритм:
        - начинаем в start;
        - на каждом шаге выбираем случайного соседа по путям (0),
          избегая немедленного разворота, если есть выбор;
        - останавливаемся, если нет соседей или достигнут max_length.

    Если маршрут короче min_length, возвращается [start] — патруль
    по сути стоит на месте.
    """
    rows_count, cols_count = len(maze), len(maze[0])

    def neighbors(cell: Coord) -> list[Coord]:
        r, c = cell
        result: list[Coord] = []
        for drow, dcol in DIRS4:
            nr, nc = r + drow, c + dcol
            if in_bounds(nr, nc, rows_count, cols_count) and maze[nr][nc] == 0:
                result.append((nr, nc))
        return result

    path: list[Coord] = [start]
    current = start

    steps_to_make = max(1, max_length - 1)
    for _ in range(steps_to_make):
        neigh = neighbors(current)
        if not neigh:
            break

        if len(path) >= 2:
            prev = path[-2]
            without_back = [cell for cell in neigh if cell != prev]
            if without_back:
                neigh = without_back

        current = rng.choice(neigh)
        path.append(current)

    if len(path) < min_length:
        return [start]

    return path


def bfs_next_step_towards(
    maze: list[list[int]],
    start: Coord,
    goal: Coord,
    blocked: set[Coord],
) -> tuple[int, int]:
    """
    Находит первый шаг по кратчайшему пути из start к goal через проходимые клетки.

    Использует обычный BFS по 4-связному графу. Стены (1) и клетки из blocked
    считаются непроходимыми.

    :param maze:
        Матрица лабиринта (0 — путь, 1 — стена).
    :param start:
        Текущая позиция (row, col).
    :param goal:
        Целевая позиция (row, col).
    :param blocked:
        Множество временно запрещённых клеток (например, блоки).
    :return:
        Сдвиг (drow, dcol) для первого шага по кратчайшему пути.
        Если пути нет или start == goal, вернёт (0, 0).
    """
    if start == goal:
        return 0, 0

    rows_count, cols_count = len(maze), len(maze[0])

    def can(cell: Coord) -> bool:
        r, c = cell
        return (
            in_bounds(r, c, rows_count, cols_count)
            and maze[r][c] == 0
            and cell not in blocked
        )

    from collections import deque

    queue: deque[Coord] = deque()
    queue.append(start)
    parents: dict[Coord, Coord] = {}
    seen: set[Coord] = {start}

    found = False
    while queue:
        row, col = queue.popleft()
        if (row, col) == goal:
            found = True
            break
        for drow, dcol in DIRS4:
            nr, nc = row + drow, col + dcol
            nxt = (nr, nc)
            if nxt not in seen and can(nxt):
                seen.add(nxt)
                parents[nxt] = (row, col)
                queue.append(nxt)

    if not found:
        return 0, 0

    # Восстанавливаем первый шаг от start к goal.
    step_cell = goal
    while parents.get(step_cell) != start:
        parent = parents.get(step_cell)
        if parent is None:
            # защитный случай: что-то пошло не так — не двигаемся
            return 0, 0
        step_cell = parent

    drow = step_cell[0] - start[0]
    dcol = step_cell[1] - start[1]
    return drow, dcol


def slime_move(
    maze: list[list[int]],
    enemy: Enemy,
    _player_pos: Coord,
    rng: random.Random,
    blocked: set[Coord],
) -> tuple[int, int]:
    """
    Стратегия движения для SLIME.

    Поведение:
        Простое случайное блуждание по коридорам с «памятью» направления:
        держим курс в трубе, на развилках случайно выбираем направление
        (избегая разворота).
    """
    return choose_enemy_direction(
        maze,
        enemy.pos[0],
        enemy.pos[1],
        enemy.direction,
        rng,
        blocked=blocked,
    )


def medium_move(
    maze: list[list[int]],
    enemy: Enemy,
    player_pos: Coord,
    rng: random.Random,
    blocked: set[Coord],
) -> tuple[int, int]:
    """
    Стратегия движения для MEDIUM.

    Сейчас повторяет поведение SLIME, но с более высокой скоростью
    (speed задаётся в ENEMY_PARAMS). В будущем сюда можно добавить
    дополнительные эвристики (избегание тупиков и т.п.).
    """
    return slime_move(maze, enemy, player_pos, rng, blocked)


def hunter_move(
    maze: list[list[int]],
    enemy: Enemy,
    player_pos: Coord,
    rng: random.Random,
    blocked: set[Coord],
) -> tuple[int, int]:
    """
    Стратегия движения для HUNTER.

    Поведение:
        - Если игрок далеко (вне aggro_radius) — ведём себя как SLIME.
        - Если игрок близко — строим кратчайший путь (BFS) и делаем первый
          шаг по нему.
        - Если путь не найден (например, всё перекрыто блоками) —
          fallback к поведению SLIME.
    """
    params = ENEMY_PARAMS[enemy.type]
    aggro_radius = params.aggro_radius
    if aggro_radius <= 0:
        return slime_move(maze, enemy, player_pos, rng, blocked)

    row, col = enemy.pos
    player_row, player_col = player_pos
    dist_to_player = abs(row - player_row) + abs(col - player_col)
    if dist_to_player > aggro_radius:
        return slime_move(maze, enemy, player_pos, rng, blocked)

    drow, dcol = bfs_next_step_towards(
        maze,
        start=enemy.pos,
        goal=player_pos,
        blocked=blocked,
    )
    if (drow, dcol) == (0, 0):
        # пути нет или мы уже стоим на игроке — используем рандомное
        # блуждание как деградацию
        return slime_move(maze, enemy, player_pos, rng, blocked)

    return drow, dcol



def patroller_move(
    maze: list[list[int]],
    enemy: Enemy,
    player_pos: Coord,
    rng: random.Random,
    blocked: set[Coord],
) -> tuple[int, int]:
    """
    Стратегия движения для PATROLLER.

    Поведение:
        - Идёт по заранее построенному маршруту patrol_path;
        - Двигается по нему туда-обратно (ping-pong);
        - Если следующая точка маршрута временно заблокирована, стоит на
          месте и ждёт;
        - Если маршрут недоступен/сломался, деградирует до medium_move.
    """
    del player_pos  # патрульный игрока не учитывает

    path = enemy.patrol_path
    if not path or len(path) < 2:
        # нет нормального маршрута — ведём себя как обычный средний враг
        return medium_move(maze, enemy, enemy.pos, rng, blocked)

    rows_count, cols_count = len(maze), len(maze[0])

    def can(cell: Coord) -> bool:
        r, c = cell
        return (
            in_bounds(r, c, rows_count, cols_count)
            and maze[r][c] == 0
            and cell not in blocked
        )

    # удостоверимся, что индекс согласован с текущей позицией
    if enemy.pos not in path:
        # что-то пошло не так — сброс маршрута
        enemy.patrol_path = [enemy.pos]
        enemy.patrol_index = 0
        enemy.patrol_direction = 1
        return 0, 0

    if path[enemy.patrol_index] != enemy.pos:
        try:
            enemy.patrol_index = path.index(enemy.pos)
        except ValueError:
            enemy.patrol_path = [enemy.pos]
            enemy.patrol_index = 0
            enemy.patrol_direction = 1
            return 0, 0

    idx = enemy.patrol_index
    direction_flag = enemy.patrol_direction

    next_idx = idx + direction_flag
    if not (0 <= next_idx < len(path)):
        # разворачиваемся на конце маршрута
        direction_flag = -direction_flag
        enemy.patrol_direction = direction_flag
        next_idx = idx + direction_flag
        if not (0 <= next_idx < len(path)):
            return 0, 0

    target = path[next_idx]
    if not can(target):
        # следующая точка маршрута временно недоступна — ждём
        return 0, 0

    drow = target[0] - enemy.pos[0]
    dcol = target[1] - enemy.pos[1]

    # индекс маршрута обновляем только если цель достижима
    enemy.patrol_index = next_idx
    return drow, dcol



#: Отображение типа врага в стратегию движения.
MOVE_STRATEGIES: dict[EnemyType, MoveStrategy] = {
    EnemyType.SLIME: slime_move,
    EnemyType.MEDIUM: medium_move,
    EnemyType.HUNTER: hunter_move,
    EnemyType.PATROLLER: patroller_move,
}


def build_safe_zone(maze: list[list[int]], start: Coord, max_steps: int) -> set[Coord]:
    """
    Возвращает множество клеток, достижимых из start за <= max_steps ходов
    по путям (0).

    Используется как «санитарная зона» для спауна врагов/монет/блоков.
    """
    rows_count, cols_count = len(maze), len(maze[0])
    queue: deque[tuple[Coord, int]] = deque([(start, 0)])
    seen: set[Coord] = {start}
    zone: set[Coord] = {start}

    while queue:
        (row, col), dist = queue.popleft()
        if dist == max_steps:
            continue
        for drow, dcol in DIRS4:
            nr, nc = row + drow, col + dcol
            if (
                in_bounds(nr, nc, rows_count, cols_count)
                and maze[nr][nc] == 0
                and (nr, nc) not in seen
            ):
                seen.add((nr, nc))
                zone.add((nr, nc))
                queue.append(((nr, nc), dist + 1))

    return zone
