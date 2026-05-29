# Project Structure

## Purpose

This document describes the current Maze Game layout and the realistic near-term grouping direction.

The project is intentionally still in an incremental refactor phase. Massive file moving is postponed on purpose to keep runtime risk low while architecture knowledge and test coverage are still being built up.

## Current structure

### Root modules

The repository root still contains the main runtime modules:

- `game_app.py`: pygame bootstrap and FSM wiring
- `maze_game.py`: main gameplay runtime loop
- `session_controller.py`: session coordination and run recording
- `players.py`, `leaderboard.py`, `db_manager.py`: persistence and query logic
- support modules such as `ui.py`, `sounds.py`, `sprites.py`, `maze_gen.py`, `coins.py`, `enemies.py`, `blocks.py`, `effects.py`, `palette.py`, `grid_utils.py`

This flat layout is still the current production reality.

### `gameplay/`

Current role:

- pure gameplay-domain helpers extracted from runtime-heavy modules

Current contents:

- `formatting.py`
- `scoring.py`

This folder is intentionally small. It is not a generic dumping ground.

### `state_machine/`

Current role:

- menu and setup screens
- FSM state protocol and manager

This is the presentation/navigation side of the current app shell.

### `tests/`

Current role:

- focused unit tests for pure deterministic logic

Current contents are intentionally limited to formatting and scoring tests.

### `docs/`

Current role:

- architecture documentation
- project-state snapshots
- refactor rules
- session history

### `resources/`

Current role:

- runtime assets such as images and audio files

## Planned near-term grouping

These are realistic grouping directions, not a commitment to immediate file moves.

### `infrastructure/` (planned)

Near-term candidate zone for:

- environment-adjacent technical modules
- persistence bootstrap helpers
- low-level integration code

Examples of likely future candidates:

- `db_manager.py`

This is only a grouping direction for future stabilization work. No file moves are implied by this document.

### `runtime/` (planned)

Near-term candidate zone for:

- active gameplay orchestration
- game session runtime models
- loop coordination code

Examples of likely future candidates:

- parts of `maze_game.py`
- possibly `game_app.py` helpers if later split becomes justified

Again, this is a future grouping direction, not a current architecture claim.

### `presentation/` (planned)

Near-term candidate zone for:

- pygame rendering helpers
- menus and screen-level UI logic

Examples of likely future candidates:

- `ui.py`
- possibly some screen-support helpers if extracted later

## Incremental refactor policy

- Current refactor work is incremental.
- Runtime files are not being moved en masse.
- New grouping should start from already-extracted pure logic or clearly isolated modules.
- Large package-wide reorganization is intentionally postponed until:
  - more pure logic is extracted
  - more tests exist
  - runtime boundaries are better documented
