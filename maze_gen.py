"""Maze generation utilities for Maze Game (Wilson UST + grid helpers)."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, Iterable, List, Tuple, Optional
import random

from grid_utils import in_bounds

Coord = Tuple[int, int]
Edge = Tuple[Coord, Coord]
Adjacency = Dict[Coord, List[Coord]]


def canonical_edge(a: Coord, b: Coord) -> Edge:
    """Вернёт ребро с лексикографически отсортированными концами (без sorted())."""
    return (a, b) if a <= b else (b, a)


# ---------- базовый граф: решётка m×n ----------


def grid_nodes(rows: int, cols: int) -> List[Coord]:
    """
    Вернёт список координат клеток решётки размера rows×cols.

    :param rows: количество строк (m)
    :param cols: количество столбцов (n)
    :return: список (row, col) для 0 <= row < rows, 0 <= col < cols
    """
    return [(row, col) for row in range(rows) for col in range(cols)]


def grid_adjacency(rows: int, cols: int) -> Adjacency:
    """
    Возвращает список соседей (4-связность) для каждой клетки решётки rows×cols.
    """
    adjacency: Adjacency = defaultdict(list)
    for row in range(rows):
        for col in range(cols):
            node = (row, col)
            if row + 1 < rows:
                neighbor = (row + 1, col)
                adjacency[node].append(neighbor)
                adjacency[neighbor].append(node)
            if col + 1 < cols:
                neighbor = (row, col + 1)
                adjacency[node].append(neighbor)
                adjacency[neighbor].append(node)
    return adjacency


# ---------- Wilson: равномерное остовное дерево ----------


def wilson_grid(
    rows: int,
    cols: int,
    *,
    seed: Optional[int] = None,
    root: Optional[Coord] = None,
    rng: Optional[random.Random] = None,
) -> List[Edge]:
    """
    Построит равномерно случайное остовное дерево (Uniform Spanning Tree) методом Уилсона.

    Идея: для всех вершин вне текущего дерева выполняем loop-erased random walk (LERW)
    до вхождения в дерево; путь добавляем в остов. Получаем честное равномерное
    распределение.

    :param rows: количество строк решётки
    :param cols: количество столбцов решётки
    :param seed: опционально — зерно для внутреннего генератора случайных чисел
    :param root: опционально — фиксированный корень дерева (клетка), иначе случайный
    :param rng: опционально — внешний random.Random (если задан, игнорируем seed)
    :return: список рёбер остова длиной rows*cols - 1
    """
    random_gen = rng or random.Random(seed)
    adjacency = grid_adjacency(rows, cols)
    all_nodes = set(grid_nodes(rows, cols))

    root_cell = root if root is not None else random_gen.choice(list(all_nodes))
    in_tree: set[Coord] = {root_cell}
    tree_edges: List[Edge] = []

    start_nodes = [node for node in all_nodes if node != root_cell]
    random_gen.shuffle(start_nodes)

    for start_node in start_nodes:
        if start_node in in_tree:
            continue

        # loop-erased RW через таблицу next_step: повторный заход в вершину
        # просто перезаписывает шаг и тем самым стирает цикл
        next_step: Dict[Coord, Coord] = {}
        current = start_node
        while current not in in_tree:
            next_cell = random_gen.choice(adjacency[current])
            next_step[current] = next_cell
            current = next_cell

        # восстановим путь и присоединим к дереву
        current = start_node
        while current not in in_tree:
            next_cell = next_step[current]
            tree_edges.append((current, next_cell))
            in_tree.add(current)
            current = next_cell
        in_tree.add(current)

    assert len(tree_edges) == rows * cols - 1
    return tree_edges


# ---------- из остова в лабиринт ----------


def tree_to_maze(
    rows: int,
    cols: int,
    tree_edges: Iterable[Edge],
    *,
    extra_openings: int = 0,
    seed: Optional[int] = None,
    rng: Optional[random.Random] = None,
) -> List[List[int]]:
    """
    Превращает остов (на решётке rows×cols) в бинарный лабиринт (1 — стена, 0 — путь).

    Дополнительно можно пробить extra_openings лишних отверстий между соседними
    «камерами», которые не входили в остов.
    """
    _rng = rng or random.Random(seed)
    maze_height, maze_width = 2 * rows + 1, 2 * cols + 1
    maze: List[List[int]] = [[1] * maze_width for _ in range(maze_height)]

    # внутренние «камеры»
    for cell_row in range(rows):
        for cell_col in range(cols):
            maze[2 * cell_row + 1][2 * cell_col + 1] = 0

    # пробиваем стены по рёбрам остова
    in_tree_edges: set[Edge] = set()
    for (row1, col1), (row2, col2) in tree_edges:
        maze[row1 + row2 + 1][col1 + col2 + 1] = 0
        in_tree_edges.add(canonical_edge((row1, col1), (row2, col2)))

    # кандидаты для дополнительных отверстий
    candidates: List[tuple[int, int, int, int]] = []
    for cell_row in range(rows):
        for cell_col in range(cols):
            if cell_row + 1 < rows:
                e = canonical_edge((cell_row, cell_col), (cell_row + 1, cell_col))
                if e not in in_tree_edges:
                    candidates.append((cell_row, cell_col, cell_row + 1, cell_col))
            if cell_col + 1 < cols:
                e = canonical_edge((cell_row, cell_col), (cell_row, cell_col + 1))
                if e not in in_tree_edges:
                    candidates.append((cell_row, cell_col, cell_row, cell_col + 1))

    _rng.shuffle(candidates)
    for row1, col1, row2, col2 in candidates[:extra_openings]:
        maze[row1 + row2 + 1][col1 + col2 + 1] = 0

    return maze


# ---------- вход/выход + проверка сквозного пути ----------


def set_entrance_exit_and_check(
    maze: List[List[int]],
    *,
    entry: Tuple[str, int] = ("left", 0),
    exit_: Tuple[str, int] = ("right", 0),
) -> Tuple[Coord, Coord, bool]:
    """
    Открывает вход/выход на границе и проверяет, что между ними есть путь по нулям.

    :param maze: бинарный лабиринт (1 — стена, 0 — путь)
    :param entry: сторона и индекс клетки входа (например, ("left", 0))
    :param exit_: сторона и индекс выхода
    :return: (коорд. границы входа, коорд. границы выхода, есть_ли_путь)
    """
    maze_rows, maze_cols = len(maze), len(maze[0])

    def _open_border(side: str, index: int) -> Tuple[Coord, Coord]:
        if side == "left":
            maze[2 * index + 1][0] = 0
            return (2 * index + 1, 0), (2 * index + 1, 1)
        if side == "right":
            maze[2 * index + 1][maze_cols - 1] = 0
            return (2 * index + 1, maze_cols - 1), (2 * index + 1, maze_cols - 2)
        if side == "top":
            maze[0][2 * index + 1] = 0
            return (0, 2 * index + 1), (1, 2 * index + 1)
        if side == "bottom":
            maze[maze_rows - 1][2 * index + 1] = 0
            return (maze_rows - 1, 2 * index + 1), (maze_rows - 2, 2 * index + 1)
        raise ValueError(f"Unsupported side: {side!r}")

    entry_border, entry_inner = _open_border(*entry)
    exit_border, exit_inner = _open_border(*exit_)

    def _reachable(start: Coord, goal: Coord) -> bool:
        queue: deque[Coord] = deque([start])
        seen: set[Coord] = {start}
        while queue:
            row, col = queue.popleft()
            if (row, col) == goal:
                return True
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                next_row, next_col = row + drow, col + dcol
                if (
                    in_bounds(next_row, next_col, maze_rows, maze_cols)
                    and maze[next_row][next_col] == 0
                    and (next_row, next_col) not in seen
                ):
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
        return False

    is_path_ok = _reachable(entry_inner, exit_inner)
    return entry_border, exit_border, is_path_ok


# ---------- проверки ----------


def is_spanning_tree(edges: Iterable[Edge], rows: int, cols: int) -> bool:
    """
    Быстрая проверка: у дерева ровно rows*cols - 1 рёбер и граф связен одной компонентой.
    """
    edges_list = list(edges)
    nodes = grid_nodes(rows, cols)
    if len(edges_list) != len(nodes) - 1:
        return False

    adjacency: Adjacency = defaultdict(list)
    for from_node, to_node in edges_list:
        adjacency[from_node].append(to_node)
        adjacency[to_node].append(from_node)

    start_node = nodes[0]
    seen: set[Coord] = {start_node}
    queue: deque[Coord] = deque([start_node])

    while queue:
        node = queue.popleft()
        for neighbor_node in adjacency[node]:
            if neighbor_node not in seen:
                seen.add(neighbor_node)
                queue.append(neighbor_node)

    return len(seen) == len(nodes)
