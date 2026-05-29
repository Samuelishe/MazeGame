# Maze Game

Small pygame maze game with menu screens, player profiles, leaderboard, procedural maze generation, enemies, coins, and SQLite-backed run history.

The project currently runs on Python 3.14 with `pygame-ce` as a drop-in replacement for `pygame`.

## Project structure

- `game_app.py` - app bootstrap and FSM wiring
- `maze_game.py` - gameplay runtime loop
- `gameplay/` - pure gameplay-domain helpers
- `state_machine/` - menu and setup screens
- `tests/` - unit tests for pure logic
- `session_controller.py` - current session and run recording
- `players.py`, `leaderboard.py`, `db_manager.py` - persistence layer
- `resources/` - images and audio assets
- `docs/` - project documentation for future maintenance and agent work

## Persistence

Current persistent files:

- `maze_stats.db` - SQLite data for players, runs, and aggregates
- `highscore.json` - legacy highscore file still updated by gameplay

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
