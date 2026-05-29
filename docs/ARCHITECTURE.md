# Architecture

## Top-level shape

The project is a single-process pygame application with a lightweight FSM shell around a large gameplay function.

There are three main layers:

1. App shell and screen navigation
2. Gameplay runtime
3. Persistence and player/session data

For inspection purposes, the current codebase can be classified more precisely into:

1. runtime orchestration
2. state machine screens
3. gameplay/domain helpers
4. domain data models
5. pygame presentation/media helpers
6. persistence and migration modules

There is now an early sublayer for pure gameplay-domain helpers under `gameplay/`. It is intentionally small and only hosts logic already reused across runtime and read-only screens.

Current runtime environment assumptions are part of the architecture:

- Python `3.14`
- local project environment: `.venv`
- rendering/input library import path: `pygame`
- installed compatible package: `pygame-ce`

## Entrypoints

- Primary entrypoint: `game_app.py`
- Public launch path today: `.\.venv\Scripts\python.exe game_app.py`
- No package-style CLI or installer entrypoint exists

## Pygame lifecycle

Current lifecycle is:

1. `game_app.run_game_app()` calls `pygame.init()`
2. Window size is derived from `maze_game.compute_window_size()`
3. Display is created once with `pygame.display.set_mode(...)`
4. `StateManager` is created and seeded with `MainMenuState`
5. Main app loop runs forever:
   - `clock.tick(60)`
   - poll `pygame.event.get()`
   - route events into current state
   - update current state
   - render current state
   - `pygame.display.flip()`
6. `quit_game()` calls `pygame.quit()` and `sys.exit(0)`

Important detail: gameplay is not a normal FSM state. `GameplayWrapper.start_level()` directly calls `maze_game.play_maze()`, which runs its own nested event/render loop until the run ends. Automatic replay/next-round progression is coordinated by an explicit loop inside `GameplayWrapper.start_level()`, not by recursive self-calls.

## State machine and screen flow

`state_machine/state_base.py` defines:

- `BaseState` protocol
- `StateManager` with `change_state`, `handle_event`, `update`, `render`

Current screens:

- `MainMenuState`
- `PlayerSelectState`
- `ModeSelectState`
- `MultiplayerSetupState`
- `LeaderboardState`

Current high-level flow:

1. `run_game_app()`
2. `init_environment()`
3. `GameSessionController.from_db(...)`
4. `make_main_menu(...)`
5. User chooses one of:
   - start game
   - leaderboard
   - change player
   - change mode
   - multiplayer setup
   - exit
6. Starting the game enters `GameplayWrapper.start_level()`
7. `start_level()` generates a maze and calls `maze_game.play_maze(...)`
8. `play_maze()` returns one of:
   - `"restart"`
   - `"new"`
   - `"menu"`
   - `"quit"`
9. `GameplayWrapper.start_level()` interprets the result and either:
   - exits app
   - returns to menu
   - advances player rotation and starts next round
   - opens player-select-before-next-round

## Gameplay runtime

`maze_game.py` owns most gameplay behavior:

- maze sizing constants
- score calculation
- level generation integration
- player movement
- enemy spawning and stepping
- temporary blocking tiles
- coin spawning and collection
- HUD rendering
- pause menu flow
- win/lose end screen flow
- runtime save hooks for highscores and session results

### Runtime state location

There is no dedicated runtime state object. Most gameplay state lives as local mutable variables and closures inside `play_maze()` and its nested `run_once()`:

- player position
- goal position
- trail
- enemies and their timers
- blocks and expiration timers
- coins and collection counters
- elapsed time baseline
- current outcome flags (`won`, `lost`)
- current direction and next movement tick

This keeps state contained to one function call, but it also makes extraction and testing harder.

## Persistence and save/data flow

### SQLite path

Primary persistent store today is `maze_stats.db`.

Main modules:

- `db_manager.py`: schema creation and connections
- `persistence/player_repository.py`: player CRUD and profile loading
- `runtime/session_stats.py`: in-memory `SessionStats`
- `players.py`: legacy compatibility shim for `SessionStats` and repository re-exports
- `session_controller.py`: in-memory session plus run recording
- `leaderboard.py`: read queries for leaderboard screens

Flow:

1. `game_app.init_environment()` calls `init_db(db_path)`
2. `GameSessionController.from_db(...)` loads or creates players
3. At end of a run, `maze_game.play_maze()` creates `RunResult`
4. `session_controller.record_run(...)` updates:
   - in-memory `SessionStats`
   - `runs`
   - `player_stats`
   - disposable-DB safety coverage now exists for this controller-level contract

### Legacy JSON path

`highscore.json` is still active.

Flow:

1. Startup calls `migrate_highscore_if_needed(...)`
2. Migration copies legacy data into SQLite once and records a flag in `meta`
3. During gameplay, `maze_game.play_maze()` still loads, updates, and saves `highscore.json`

Result: runtime persistence is split between SQLite and legacy JSON.

## Persistence Architecture

### Current persistence modules

- `db_manager.py`
  - SQLite infrastructure only: connection setup, PRAGMA, schema bootstrap, `meta` flags.
- `persistence/player_repository.py`
  - dedicated player CRUD/profile-loading repository over SQLite.
- `runtime/session_stats.py`
  - isolated runtime-only `SessionStats`.
- `players.py`
  - compatibility re-export for `SessionStats` and repository imports.
- `session_controller.py`
  - mixed module: session orchestration plus SQLite write path for completed runs.
- `leaderboard.py`
  - read-only query API over SQLite.
- `highscores.py`
  - legacy JSON read/write/update path for global highscores.
- `highscore_adapter.py`
  - one-time migration bridge from legacy JSON into SQLite.

### Current persistence flow

1. `game_app.init_environment()`:
   - computes `maze_stats.db` path;
   - calls `init_db(db_path)`;
   - calls `migrate_highscore_if_needed(db_path, legacy_player_name="Игрок 1")`.
2. `GameSessionController.from_db(db_path)`:
   - calls `init_db(db_path)` again defensively;
   - loads players through `persistence.player_repository.load_players(db_path)`;
   - creates a default player through `persistence.player_repository.get_or_create_player(...)` when needed.
3. State-machine screens mutate persistent player state indirectly:
   - `PlayerSelectState` -> `session.create_player(...)`, `session.delete_player_from_session(...)`, `session.choose_player(...)`;
   - `MultiplayerSetupState` -> `session.create_player(...)`, `session.delete_player_from_session(...)`, `session.configure_rotation_players(...)`, `session.set_mode(...)`;
   - `ModeSelectState` -> `session.set_mode(...)`;
   - `LeaderboardState` -> `get_top_scores(...)`, `get_players_sorted(...)`.
4. `maze_game.play_maze()` end-of-run flow:
   - updates legacy JSON highscores through `load_highscore(...)`, `update_highscore_if_better(...)`, `save_highscore(...)`;
   - updates in-memory session stats directly through `SessionStats.add_result(...)` when no controller is present;
   - otherwise creates `RunResult` and calls `session_controller.record_run(...)`.
5. `GameSessionController.record_run(...)`:
   - updates in-memory `SessionStats`;
   - inserts into `runs`;
   - updates aggregates in `player_stats`.

### Responsibility boundary assessment

- `db_manager.py` is a clean infrastructure boundary.
- `leaderboard.py` is a clean read-model/query boundary.
- `highscores.py` is internally coherent, but it keeps a second active persistence path alive.
- `highscore_adapter.py` is coherent as a migration module, but it encodes transitional persistence policy.
- `players.py` and `session_controller.py` are the main persistence-boundary problems:
  - `players.py` is now only a compatibility shim, but it still remains on the boundary;
  - `session_controller.py` mixes application/session orchestration with direct SQL write logic.

### Target persistence shape

The project does not need enterprise layering. A realistic target is:

- `persistence/db_manager.py`
  - SQLite bootstrap, connection, PRAGMA, meta flags
- `persistence/player_repository.py`
  - CRUD and profile-loading operations over `players` / `player_stats`
- `persistence/run_repository.py`
  - append completed runs and update aggregates
- `persistence/leaderboard_queries.py`
  - read-only leaderboard queries
- `persistence/legacy_highscores.py`
  - runtime JSON compatibility path while it still exists
- `persistence/migrations/highscore_adapter.py`
  - one-time legacy migration
- `domain/player_models.py`
  - `PlayerProfile`, `PlayerAggregateStats`
- `application/session_controller.py`
  - current-player rotation, mode management, session-level orchestration
- `application/session_stats.py` or `domain/session_stats.py`
  - in-memory `SessionStats`

This is a target ownership map only. No file moves are implied yet.

### `players.py` decomposition analysis

`players.py` currently contains two direct responsibility slices:

1. transitional compatibility re-export
   - `SessionStats`
   - `load_players(...)`
   - `create_player(...)`
   - `delete_player(...)`
   - `get_player_by_name(...)`
   - `get_or_create_player(...)`

The pure player models now live separately in `domain/player_models.py`, the repository implementation now lives in `persistence/player_repository.py`, and `SessionStats` now lives in `runtime/session_stats.py`.

This means the file is no longer an ownership module. What remains is compatibility imports for old call sites.

Dependency pressure inside the project:

- `session_controller.py` depends on:
  - `PlayerProfile`
  - `SessionStats`
  - repository CRUD/bootstrap functions
- `maze_game.py` depends on:
  - `SessionStats` only
- `state_machine/player_select_state.py` and `state_machine/multiplayer_setup_state.py` depend on:
  - `PlayerProfile` for local typed player lists
- `highscore_adapter.py` depends on:
  - `get_or_create_player(...)`

The next clean future cut is:

- remove the temporary re-export from `players.py` after imports are fully narrowed.

### `SessionStats` analysis

Current direct consumers:

- `maze_game.play_maze(...)`
  - gets `SessionStats` from `GameSessionController` when a controller exists;
  - otherwise creates a standalone `SessionStats()` for controller-free mode;
  - writes through `add_result(...)`;
  - reads through `summary_line()`.
- `GameSessionController`
  - stores `SessionStats` objects in `session_stats_by_player`;
  - creates them during bootstrap, player creation, and rotation reconfiguration;
  - updates them in `record_run(...)`.

No direct imports were found in:

- `game_app.py`
- `leaderboard.py`
- `highscore_adapter.py`
- `state_machine/*`

Boundary interpretation:

- `SessionStats` is not a persistence model because it is never stored directly in SQLite or JSON.
- `SessionStats` is not a service object because it has no external coordination responsibility.
- `SessionStats` is best treated as mutable runtime session state: an in-memory per-player aggregate for the current process lifetime.

Dependency profile:

- stdlib only (`dataclass`);
- no dependency on SQLite;
- no dependency on pygame;
- no dependency on `PlayerProfile`;
- no dependency on repository APIs.

Placement options:

- Keep in `players.py`
  - lowest immediate risk
  - weakest ownership clarity
- Move to `domain/`
  - physically clean, but semantically weaker because the object is session-lifetime runtime state rather than stable domain data
- Move to `runtime/` or a later `application/`-style package
  - best ownership fit for current usage pattern
  - requires one more package-boundary step first

Recommended direction:

- completed: `SessionStats` now lives in `runtime/session_stats.py`;
- broader runtime package migration is still deferred.

## Module responsibilities

### Architectural categories

- Runtime orchestration:
  `game_app.py`, `maze_game.py`
- State machine:
  `state_machine/state_base.py`, `state_machine/main_menu.py`,
  `state_machine/player_select_state.py`, `state_machine/mode_select_state.py`,
  `state_machine/multiplayer_setup_state.py`, `state_machine/leaderboard_state.py`
- Gameplay/domain:
  `domain/player_models.py`, `maze_gen.py`, `grid_utils.py`, `enemies.py`, `gameplay/*`
- Mixed gameplay + presentation support:
  `coins.py`, `blocks.py`
- Presentation/media:
  `ui.py`, `sounds.py`, `sprites.py`, `effects.py`, `palette.py`
- Persistence/data:
  `db_manager.py`, `persistence/player_repository.py`, `players.py`, `session_controller.py`, `leaderboard.py`,
  `highscores.py`, `highscore_adapter.py`

### App shell

- `game_app.py`: bootstrap, navigation wiring, session creation, gameplay handoff

### FSM screens

- `state_machine/main_menu.py`: main menu UI
- `state_machine/player_select_state.py`: choose/create/delete player
- `state_machine/mode_select_state.py`: select `RoundMode`
- `state_machine/multiplayer_setup_state.py`: choose rotation participants
- `state_machine/leaderboard_state.py`: render leaderboard data

### Gameplay support

- `gameplay/formatting.py`: pure time-formatting helper shared by gameplay and leaderboard UI
- `gameplay/hud_text.py`: pure HUD text builders used by gameplay rendering without owning pygame surfaces
- `gameplay/maze_positions.py`: pure border-to-inner-cell translation helper used by gameplay entry/exit setup
- `gameplay/result_text.py`: pure end-screen text builders plus deterministic end-summary value preparation used by gameplay summary rendering
- `gameplay/scoring.py`: pure score parameters, score-input preparation, and score calculation logic
- `maze_gen.py`: maze generation
- `grid_utils.py`: shared grid helpers
- `enemies.py`: enemy models, schemes, movement strategies
- `coins.py`: mixed module with coin spawning plus coin rendering
- `blocks.py`: mixed module with block spawn/respawn plus block rendering
- `effects.py`: visual effects
- `palette.py`: color palette generation
- `sprites.py`: sprite sheet helpers
- `sounds.py`: audio loading/fallback generation
- `ui.py`: text rendering and pause/end overlays; its mixed-text renderer is now also reused by gameplay HUD surface rendering

### Data/persistence

- `db_manager.py`: SQLite schema and connection setup
- `persistence/player_repository.py`: player repository CRUD/profile loading
- `runtime/session_stats.py`: in-memory session aggregate
- `players.py`: compatibility shim for `SessionStats` and repository re-exports
- `session_controller.py`: current session coordination plus SQLite run recording
- `leaderboard.py`: leaderboard queries
- `highscores.py`: legacy JSON highscore read/write
- `highscore_adapter.py`: one-time migration bridge

### Testing

- `tests/`: focused unit tests for pure logic extracted from runtime-heavy modules
- `tests/test_player_repository.py`: focused disposable-DB smoke coverage for the isolated player repository boundary
- `tests/test_session_controller_record_run.py`: disposable-DB safety coverage for the current `GameSessionController.record_run(...)` contract before future `run_repository` extraction

## Coupling map

Main dependency spine:

- `game_app.py` -> `state_machine/*`
- `game_app.py` -> `session_controller.py`
- `game_app.py` -> `maze_game.py`
- `maze_game.py` -> gameplay helpers (`coins`, `enemies`, `blocks`, `ui`, `sounds`, `sprites`, `maze_gen`)
- `maze_game.py` -> `session_controller.py`
- `session_controller.py` -> `persistence/player_repository.py`, `runtime/session_stats.py`, `db_manager.py`
- `persistence/player_repository.py` -> `db_manager.py`
- `leaderboard.py` -> `db_manager.py`
- `state_machine/leaderboard_state.py` -> `leaderboard.py`

Notable dependency smell:

- `maze_game.py` still remains the main gameplay concentration point, but pure formatting/scoring logic has been extracted into `gameplay/` to reduce incidental coupling.
- `ui.py` is shared by both gameplay runtime and state-machine screens, so presentation concerns are still centralized in one broad helper module.
- `players.py` is now only a compatibility shim and should not stay as a long-term ownership module.
- `coins.py` and `blocks.py` mix gameplay-domain spawning with pygame rendering helpers.

## Cyclic imports

Based on the current import structure, no direct Python cyclic import was found among project modules.

That said, coupling is still high because several UI and runtime paths depend on `maze_game.py` as a utility host.

## Architectural bottlenecks

1. `maze_game.py` is the dominant god module.
2. `game_app.py` mixes bootstrap, flow orchestration, menu content, and gameplay transition logic.
3. Save logic is split between SQLite and JSON.
4. Nested pygame loops make control flow harder to reason about than pure FSM states.
5. There is no dedicated runtime model for a round.
6. Root-level module count is still high, so ownership boundaries are visually weak.
7. Several modules combine domain logic with rendering or persistence details.

## Current target structure direction

The recommended future package shape is:

- `runtime/`
  - app startup
  - gameplay loop coordination
  - round flow orchestration
- `state_machine/`
  - FSM primitives and screen states
- `domain/`
  - maze generation
  - scoring
  - enemy logic
  - grid/gameplay pure helpers
- `presentation/`
  - pygame rendering helpers
  - overlays
  - sprites
  - audio
  - visual effects
- `persistence/`
  - SQLite setup
  - repositories and queries
  - legacy JSON adapter/migration code

This is a planning target only. No file moves are implied by this document yet.

## Runtime Boundary Analysis

### Runtime concerns visible in current code

The codebase already has a real runtime slice, even though it is not packaged as `runtime/` yet.

That slice currently includes:

- pygame process lifecycle and main loop
- FSM state switching and screen flow
- gameplay round execution
- active-player selection and round-rotation policy
- session-lifetime in-memory aggregates
- current-run mutable state and end-of-run branching

Concrete runtime entities:

- `GameplayWrapper`
- `GameSessionController`
- `RoundMode`
- `RunResult`
- `SessionStats`
- local mutable run state inside `maze_game.play_maze()`

### Runtime-related file map

- `game_app.py`
  - outer runtime shell
  - owns pygame bootstrap, FSM loop, gameplay handoff, and next-round policy
- `maze_game.py`
  - inner runtime shell for one active run
  - owns current-run state, nested event loop, pause/end flow, and runtime save branching
- `session_controller.py`
  - session-level runtime/application coordination with persistence write behavior mixed in
- `runtime/session_stats.py`
  - isolated runtime-only session aggregate object
- `players.py`
  - compatibility-only shim, no longer a true runtime owner
- `state_machine/*`
  - user-facing runtime screens running under the outer loop

### What should not be considered runtime

- `domain/player_models.py`
  - durable typed models, not runtime flow
- `gameplay/*`
  - pure helper logic, not runtime orchestration
- `persistence/player_repository.py`
  - persistence boundary only
- `db_manager.py`
  - infrastructure only
- `leaderboard.py`
  - query/read-model boundary
- `highscores.py`
  - legacy persistence path

### Should `runtime/` be introduced now

Current recommendation: partially completed.

Reasoning:

- the first narrow runtime-oriented move is done: `SessionStats` now has a dedicated home;
- but broader runtime file moves are still too coupled for one safe pass.

### Safe staged path

1. keep documenting runtime concerns explicitly
2. completed: move `SessionStats` into a runtime-oriented module in a narrow pass
3. only then consider broader runtime package moves for orchestration classes and modules

## Run Recording Boundary Analysis

### Current flow

The current end-of-run persistence flow is:

1. `maze_game.play_maze(...)`
   - prepares final runtime values
   - computes score
   - updates legacy `highscore.json` separately
2. `maze_game.play_maze(...)`
   - constructs `RunResult` when a `GameSessionController` exists
3. `maze_game.play_maze(...)`
   - calls `GameSessionController.record_run(...)`
4. `GameSessionController.record_run(...)`
   - updates `SessionStats`
   - inserts one row into `runs`
   - updates one row in `player_stats`

### What `record_run(...)` currently mixes

- runtime/application orchestration
  - obtains per-player session aggregate
  - applies one completed-run result to in-memory state
- persistence write logic
  - opens SQLite connection
  - inserts into `runs`
  - updates aggregate row in `player_stats`
- application-level aggregate policy
  - `best_time_ms` changes only on win
  - wins/deaths are derived from `result.won`

### Best current extraction boundary

The most natural next split is:

- keep `GameSessionController` as orchestration owner
- move the SQL write path behind a persistence-facing boundary

That points to a future `persistence/run_repository.py` rather than to a broader service layer.

### Option assessment

- Option A: keep `record_run(...)` in `GameSessionController`
  - safest short-term
  - weakest boundary improvement
- Option B: move SQL write path into `persistence/run_repository.py`
  - best fit for current architecture
  - consistent with `persistence/player_repository.py`
- Option C: move whole run-recording flow into a separate recorder/service
  - broader than needed right now
  - higher chance of premature service layering

### Recommended direction

Recommend Option B.

This keeps:

- runtime/session ownership in `GameSessionController`
- persistence write details in a dedicated persistence module

without changing the public gameplay flow or inventing a wider abstraction than the current code needs.
