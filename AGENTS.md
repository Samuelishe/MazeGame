# AGENTS.md

Primary onboarding file for future AI-agent work in this project.

## Scope and constraints

- Work only inside `C:\Users\Oleg Zudin\PycharmProjects\MazeGame`.
- Do not touch sibling projects or `Project_for_study_and_tests`.
- Do not create or switch virtual environments.
- Use only this interpreter:
  `C:\Users\Oleg Zudin\PycharmProjects\MazeGame\.venv\Scripts\python.exe`
- Do not rename modules or restructure the project without explicit approval.
- Treat gameplay stability as the primary constraint.

## Fast start

1. Read [docs/INDEX.md](docs/INDEX.md).
2. Read [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md).
3. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) before changing runtime flow.
4. Read [docs/TECH_DEBT.md](docs/TECH_DEBT.md) before proposing refactors.
5. Read [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) before moving or grouping files.
6. Append important work notes to [docs/SESSION_LOG.md](docs/SESSION_LOG.md).

## Current runtime entrypoint

- Main entrypoint: `game_app.py`
- Launch command:
  `C:\Users\Oleg Zudin\PycharmProjects\MazeGame\.venv\Scripts\python.exe game_app.py`

## Environment notes

- The project currently runs on Python `3.14` in the local `.venv`.
- The runtime dependency is `pygame-ce`, used as a drop-in replacement imported in code as `pygame`.
- Test command:
  `C:\Users\Oleg Zudin\PycharmProjects\MazeGame\.venv\Scripts\python.exe -m pytest tests`

## Current architecture in one screen

- `game_app.py`: pygame bootstrap, FSM wiring, session creation, app loop.
- `state_machine/`: menu and setup screens.
- `gameplay/`: pure gameplay-domain helpers extracted from runtime-heavy modules.
- `maze_game.py`: actual gameplay loop, rendering, input, scoring, enemy/block/coin orchestration.
- `session_controller.py`: in-memory session and SQLite write path for completed runs.
- `players.py`, `leaderboard.py`, `db_manager.py`: persistence and query layer.
- `highscores.py`, `highscore_adapter.py`: legacy JSON highscore plus one-time migration into SQLite.
- `ui.py`, `sounds.py`, `sprites.py`: support services for rendering and media.
- `tests/`: focused unit tests for pure logic.

## Known high-risk zones

- `maze_game.py` is the main god module and the highest-risk change surface.
- `game_app.py` contains gameplay orchestration and recursive round restarts.
- Runtime persistence currently writes to both `maze_stats.db` and `highscore.json`.
- Pygame event handling is split between the app FSM loop and nested loops inside gameplay/pause/end screens.

## Rules for safe changes

- Keep changes local and reversible.
- Prefer documentation, tests, and narrow bug fixes over restructuring.
- Extract helpers only when behavior is preserved and ownership becomes clearer.
- If changing gameplay flow, document old and new flow in `docs/SESSION_LOG.md`.
- If changing save behavior, document whether SQLite, JSON, or both are touched.

## Verification baseline

- At minimum, run syntax validation with the project interpreter.
- For runtime checks, use the project interpreter only.
- Do not add tooling that requires a new environment.

## Documentation update policy

Update these files when the architecture changes:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): module boundaries and flow
- [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md): current reality snapshot
- [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md): file layout and near-term grouping plan
- [docs/TECH_DEBT.md](docs/TECH_DEBT.md): risks and bottlenecks
- [docs/ROADMAP.md](docs/ROADMAP.md): next safe steps
- [docs/SESSION_LOG.md](docs/SESSION_LOG.md): dated work log
