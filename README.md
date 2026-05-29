# Maze Game

Small pygame maze game with menu screens, player profiles, leaderboard, procedural maze generation, enemies, coins, and SQLite-backed run history.

The project currently runs on Python 3.14 with `pygame-ce` as a drop-in replacement for `pygame`.

## Project structure

- `game_app.py` - app bootstrap and FSM wiring
- `maze_game.py` - gameplay runtime loop
- `gameplay/` - pure gameplay-domain helpers
- `domain/` - player domain models
- `persistence/` - repository boundaries for players and completed runs
- `runtime/` - runtime-oriented helpers such as session stats and gameplay persistence handoff
- `state_machine/` - menu and setup screens
- `tests/` - unit tests for pure logic
- `session_controller.py` - current session and run recording
- `leaderboard.py`, `db_manager.py` - read/query and SQLite bootstrap support
- `resources/` - images and audio assets
- `docs/` - project documentation for future maintenance and agent work

## Persistence

Current persistent files:

- `maze_stats.db` - main structured SQLite store for players, runs, and aggregates
- `highscore.json` - legacy compatibility output for the global highscore snapshot

Compatibility contract:

- SQLite is the main structured store used by the application.
- `highscore.json` is not the primary store after migration.
- `highscore.json` keeps one legacy global snapshot and is updated only when a run improves that snapshot.
- `highscore.json` does not provide per-player history, full leaderboard data, or a complete mirror of SQLite.
- Local SQLite artifacts such as `maze_stats.db`, `*.db-shm`, and `*.db-wal` are ignored by Git.

## Dependency

- Runtime dependency: `pygame-ce`
- Test dependency: `pytest`

## Smoke test

Create `.venv` if it does not already exist:

```powershell
py -3.14 -m venv .venv
```

Install requirements:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the game:

```powershell
.\.venv\Scripts\python.exe game_app.py
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

## Documentation

Start with:

- [AGENTS.md](AGENTS.md)
- [docs/INDEX.md](docs/INDEX.md)
- [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

## Current architecture status

The project is functional and reasonably small, but the gameplay core is concentrated in `maze_game.py`. Safe future work should focus on stabilization, tests, and incremental extraction rather than broad refactoring.
