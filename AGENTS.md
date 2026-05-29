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

## Communication rules

- All user-facing responses must be written in Russian.
- Commit messages at the end of each task must remain in English.
- Treat both rules as mandatory for all future agents working in this project.
- Every final agent response must include:
  - changed files list;
  - brief description of changes;
  - behavior changes: yes/no;
  - checks and tests;
  - risks;
  - commit message.

## Fast start

1. Read [docs/INDEX.md](docs/INDEX.md).
2. Read [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md).
3. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) before changing runtime flow.
4. Read [docs/TECH_DEBT.md](docs/TECH_DEBT.md) before proposing refactors.
5. Read [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) before moving or grouping files.
6. Append important work notes to [docs/SESSION_LOG.md](docs/SESSION_LOG.md).

## Documentation-first policy

Before any serious refactoring, an agent must:

- read the existing project documentation;
- read existing module docstrings in the relevant code;
- check [docs/MODULES.md](docs/MODULES.md);
- check [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md);
- check [docs/REFACTORING_PLAN.md](docs/REFACTORING_PLAN.md).

If an architectural decision changes, the corresponding documentation must be updated in the same task.

## Current runtime entrypoint

- Main entrypoint: `game_app.py`
- Launch command:
  `C:\Users\Oleg Zudin\PycharmProjects\MazeGame\.venv\Scripts\python.exe game_app.py`

## Environment notes

- The project currently runs on Python `3.14` in the local `.venv`.
- The runtime dependency is `pygame-ce`, used as a drop-in replacement imported in code as `pygame`.
- Test command:
  `C:\Users\Oleg Zudin\PycharmProjects\MazeGame\.venv\Scripts\python.exe -m pytest tests`
- `maze_stats.db` is treated as a disposable development/test artifact during architecture and persistence work.
- Agents may delete, recreate, reinitialize, or evolve the local DB schema when needed for persistence architecture, migration logic, testability, or correctness.
- `.gitignore` must continue ignoring `maze_stats.db`, `*.db-shm`, and `*.db-wal`.
- Never commit local SQLite artifacts.
- If the DB is deleted or recreated in a task, that must be stated explicitly in the final report.
- If schema changes may affect future user data compatibility, record that as a future migration concern.

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
- Prefer extract before rewrite.
- Prefer small safe steps.
- Prefer package boundaries before file moves.
- Prefer documentation before restructuring.
- If changing gameplay flow, document old and new flow in `docs/SESSION_LOG.md`.
- If changing save behavior, document whether SQLite, JSON, or both are touched.
- Avoid mass file moves without a plan.
- Avoid large rewrites.
- Do not change gameplay behavior without an explicit user request.

## Module visibility policy

- Every production module must be represented in project documentation.
- Keep these files aligned with the real module set:
  - [docs/MODULES.md](docs/MODULES.md)
  - [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
  - [docs/INDEX.md](docs/INDEX.md)
- If a new production module is added, document it in the same task.

## Dependency policy

- Agents may add new libraries to `requirements.txt` when they clearly improve the project.
- New dependencies are allowed when they reduce complexity, improve readability, improve testability, improve maintainability, improve user experience, or improve reliability.
- Do not add dependencies "just in case".
- Do not add heavy dependencies without clear project value.
- Do not duplicate capabilities the project already has.
- When adding a dependency, also:
  - update `requirements.txt`;
  - update `README.md` if usage or setup changes;
  - explain the reason in the final report.

## Architecture inspection policy

Before moving files between packages, an agent must:

- inspect imports;
- inspect module dependencies;
- check test impact;
- update [docs/MODULES.md](docs/MODULES.md);
- update [docs/REFACTORING_PLAN.md](docs/REFACTORING_PLAN.md).

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
