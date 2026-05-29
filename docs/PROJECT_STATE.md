# Project State

## Snapshot

Date of audit: 2026-05-29

This project is a working pygame maze game with:

- main menu
- player selection
- mode selection
- multiplayer queue setup
- leaderboard screen
- procedural maze generation
- enemies, coins, temporary block tiles
- SQLite-backed players and run history
- legacy JSON highscore compatibility
- Python 3.14-compatible `.venv` runtime with `pygame-ce`

The project also now has an explicit governance baseline for future agents:

- Russian-only user-facing communication
- English-only commit messages
- documentation-first architecture work
- mandatory module visibility in docs
- staged refactoring instead of large rewrites

## Current entrypoints

- Main entrypoint in use: `game_app.py`
- There is no separate package launcher or test harness in the repository root
- Current launch command:
  `.\.venv\Scripts\python.exe game_app.py`

## Current gameplay flow

1. App starts in `game_app.run_game_app()`
2. DB is initialized and legacy highscore migration is attempted
3. `GameSessionController` is created from SQLite state
4. Main menu is shown
5. Starting a run generates a maze and enters `maze_game.play_maze()`
6. Gameplay loop runs until:
   - pause menu requests action
   - player wins
   - player loses
   - window close event occurs
7. End-of-run logic updates:
   - `highscore.json`
   - in-memory session stats
   - SQLite run history and player aggregates if a session controller is present
8. Control returns to `game_app.GameplayWrapper`
9. Wrapper decides next action based on `RoundMode`
10. Automatic next-round progression inside `GameplayWrapper.start_level()` now uses an explicit loop instead of recursive self-calls

## Current round modes

- `RoundMode.SINGLE`
- `RoundMode.ROTATE_QUEUE`
- `RoundMode.PICK_EACH_ROUND`

Behavior today:

- `SINGLE`: same active player stays selected
- `ROTATE_QUEUE`: current player advances automatically after each completed run
- `PICK_EACH_ROUND`: player-select screen is shown between runs

## Runtime state reality

Current runtime state is not centralized. It is split across:

- `GameSessionController`: current player list, mode, session stats
- pygame globals: display, mixer, event queue, tick timing
- locals inside `maze_game.play_maze()`: active run state

There is no single `GameState` or `RunState` object today.

Runtime boundary reality:

- a real runtime slice already exists conceptually;
- it is currently spread across `game_app.py`, `maze_game.py`, `session_controller.py`, `runtime/session_stats.py`, and `state_machine/*`;
- the strongest runtime-only object identified so far is `SessionStats`, and it now has a dedicated `runtime/` home;
- a broader runtime package migration is not in place yet.

## Data stores in use

- `maze_stats.db`: authoritative structured store for players and runs
- `highscore.json`: still updated during gameplay for legacy highscore tracking

### Persistence Architecture

Current persistence flow is:

1. `game_app.init_environment()` creates/initializes SQLite and runs legacy migration.
2. `GameSessionController.from_db(...)` loads players and ensures a default player exists.
3. Menu states mutate player/session state through `GameSessionController`.
4. `LeaderboardState` reads SQLite through `leaderboard.py`.
5. `maze_game.play_maze()` writes:
   - legacy highscores to `highscore.json`;
   - SQLite run data through `session_controller.record_run(...)` when a session controller is present.

Current persistence boundary reality:

- `db_manager.py` and `leaderboard.py` are comparatively clean;
- `persistence/player_repository.py` now owns player CRUD/profile loading;
- `persistence/run_repository.py` now owns the SQLite run-write path and aggregate update logic;
- the production import graph no longer depends on `players.py`;
- `session_controller.py` is now closer to runtime/application orchestration and no longer owns raw SQL for run writes;
- runtime save behavior is still split between SQLite and legacy JSON.

Run-recording boundary reality:

- `maze_game.py` prepares `RunResult` and hands it to `GameSessionController`;
- `GameSessionController.record_run(...)` now owns runtime `SessionStats` updates and delegates SQLite writes to `persistence.run_repository`;
- `GameSessionController.record_run(...)` now has disposable-DB safety coverage on isolated temporary SQLite files;
- the SQL write path has now been extracted without changing the public `GameSessionController` contract.

SessionStats reality:

- `SessionStats` is in-memory mutable session state, not a persistence model;
- it is currently owned operationally by `GameSessionController`;
- `maze_game.py` can also instantiate it directly in controller-free mode;
- it now lives in `runtime/session_stats.py`;
- the old `players.py` compatibility shim is no longer needed by production code.

Database governance baseline:

- `maze_stats.db` is treated as a disposable development/test artifact during architecture and persistence work.
- Local `.db`, `.db-shm`, and `.db-wal` files remain ignored and must not be committed.
- If future schema changes affect user data compatibility, they must be documented as migration concerns.

## File layout summary

- Root python modules: gameplay, data, utilities
- `gameplay/`: pure gameplay-domain helpers extracted from `maze_game.py`
- `state_machine/`: all current menu/setup screens
- `tests/`: focused unit tests for pure logic
- `resources/`: images and audio assets
- `docs/`: architecture and maintenance documents

Current structure reality is still root-heavy:

- 10+ production modules still live directly in repository root
- major runtime files remain root-level
- support modules are only partially grouped
- `gameplay/` exists, but currently covers only a small pure-logic slice
- `domain/` now exists and currently hosts pure player domain models
- `persistence/` now exists and currently hosts the player repository boundary
- `runtime/` now exists, but currently contains only `SessionStats`

## External dependencies actually used

- `pygame-ce`
- `pytest` for local tests

Everything else currently imported by the codebase is from the Python standard library.

## Validation performed during audit

- Static repository inspection
- Import/dependency review
- Syntax validation with the project interpreter via `py_compile`
- focused disposable-DB repository smoke tests via `pytest` and `tmp_path`

Not performed in this audit:

- full interactive gameplay playthrough
- automated tests, because no test suite exists in the repository

## Current architecture assessment

This is a workable small-game codebase with a clear separation between menu screens and data access, but the gameplay core has outgrown its current single-file structure. The project is stable enough for incremental improvement, not for a blind refactor.

The architecture inspection confirms that the main structural issue is not broken behavior but weak physical organization:

- `maze_game.py` is still the main concentration point
- too many modules remain in the root directory
- some modules still mix domain and rendering concerns
- `players.py` has been removed after the compatibility cleanup
- repeated state-screen UI patterns are present but not yet centralized
- persistence boundaries are clearer than before, but `session_controller.py` and the active JSON/SQLite split still remain architectural hotspots

## Stabilization notes

- Recursive next-round flow in `GameplayWrapper.start_level()` has been replaced with an explicit loop.
- `play_maze()` return values and menu/pause behavior remain unchanged.
- `format_time`, `ScoreParams`, and `compute_score` now live in `gameplay/` as pure logic modules.
- Data-only score preparation for completed runs now also lives in `gameplay/scoring.py`.
- Deterministic best-time/highscore/end-summary value preparation now also lives in `gameplay/result_text.py`.
- HUD text assembly now also lives in `gameplay/` as pure helper logic, while pygame HUD rendering remains in `maze_game.py`.
- HUD mixed-text surface rendering no longer lives as a nested helper in `maze_game.py`; gameplay now reuses `ui.render_mixed_text(...)`.
- Border-to-inner-cell translation for maze entry/exit now also lives in `gameplay/maze_positions.py` as pure helper logic.
- End-screen result summary text now also lives in `gameplay/` as pure helper logic.
- The first unit tests cover formatting and scoring behavior without touching pygame runtime.
- `persistence/player_repository.py` now has minimal disposable-DB smoke coverage that uses temporary SQLite files and does not touch the working `maze_stats.db`.
- `GameSessionController.record_run(...)` now also has disposable-DB safety coverage that uses temporary SQLite files and does not touch the working `maze_stats.db`.
- Documentation and environment assumptions now point to `.venv`, `pygame-ce`, and the current pytest workflow.

## Inspection notes

The architecture inspection pass added:

- file-level module map in `docs/MODULES.md`
- staged restructuring plan in `docs/REFACTORING_PLAN.md`
- explicit target package direction for future work

No runtime code, imports, gameplay behavior, or tests were changed during this pass.

## Governance notes

Current governance rules now require:

- documentation review before serious refactoring;
- documentation updates in the same step when architecture decisions change;
- documentation coverage for every production module;
- explicit dependency justification when new libraries are added;
- import/dependency/test review before file moves between packages.
