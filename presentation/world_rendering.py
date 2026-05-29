"""World rendering helpers extracted from maze_game runtime host."""

from __future__ import annotations

import pygame

from blocks import Block
from coins import Coin
from effects import Effects
from enemies import Enemy
from presentation.block_rendering import draw_block_cell
from presentation.coin_rendering import draw_coin
from sprites import AnimatedSprite

Coord = tuple[int, int]


def render_world(
    *,
    screen: "pygame.Surface",
    maze: list[list[int]],
    maze_rows: int,
    maze_cols: int,
    cell_px: int,
    wall_rgb: tuple[int, int, int],
    path_rgb: tuple[int, int, int],
    goal_rgb: tuple[int, int, int],
    player_rgb: tuple[int, int, int],
    blocks: list[Block],
    block_pulse_ms: int,
    coins: list[Coin],
    goal: Coord,
    trail: set[Coord],
    enemies: list[Enemy],
    enemy_anims: list[AnimatedSprite],
    player: Coord,
    effects: Effects,
    now_ms: int,
) -> None:
    """Рисует весь мир в прежнем порядке слоёв без HUD и без UI-оверлеев."""
    # 1. maze/background
    screen.lock()
    for row_draw in range(maze_rows):
        y_px = row_draw * cell_px
        row_maze = maze[row_draw]
        for col_draw in range(maze_cols):
            x_px = col_draw * cell_px
            cell_rgb = path_rgb if row_maze[col_draw] == 0 else wall_rgb
            pygame.draw.rect(screen, cell_rgb, (x_px, y_px, cell_px, cell_px))
    screen.unlock()

    # 2. blocks
    for block in blocks:
        block_x_px = block.pos[1] * cell_px
        block_y_px = block.pos[0] * cell_px
        draw_block_cell(
            screen, block_x_px, block_y_px, cell_px, wall_rgb, now_ms, block_pulse_ms
        )

    # 3. coins
    for coin in coins:
        draw_coin(screen, coin, cell_px)

    # 4. goal
    goal_x_px = goal[1] * cell_px
    goal_y_px = goal[0] * cell_px
    pygame.draw.rect(
        screen,
        goal_rgb,
        (goal_x_px + cell_px * 0.2, goal_y_px + cell_px * 0.2, cell_px * 0.6, cell_px * 0.6),
        border_radius=4,
    )

    # 5. trail
    for trail_row, trail_col in trail:
        trail_x_px = trail_col * cell_px
        trail_y_px = trail_row * cell_px
        pygame.draw.rect(
            screen,
            (255, 255, 255),
            (trail_x_px + cell_px * 0.35, trail_y_px + cell_px * 0.35, cell_px * 0.3, cell_px * 0.3),
            border_radius=3,
        )

    # 6. enemies
    for enemy, anim in zip(enemies, enemy_anims):
        x_px = enemy.pos[1] * cell_px
        y_px = enemy.pos[0] * cell_px

        frame = anim.get_current_frame(now_ms)

        enemy_size = int(cell_px * 0.85)
        offset = (cell_px - enemy_size) // 2

        frame_scaled = pygame.transform.scale(frame, (enemy_size, enemy_size))
        screen.blit(frame_scaled, (x_px + offset, y_px + offset))

    # 7. player
    player_x_px = player[1] * cell_px
    player_y_px = player[0] * cell_px
    pygame.draw.rect(
        screen,
        player_rgb,
        (player_x_px + cell_px * 0.15, player_y_px + cell_px * 0.15, cell_px * 0.7, cell_px * 0.7),
        border_radius=6,
    )

    # 8. effects
    effects.draw_all(screen, cell_px, now_ms)
