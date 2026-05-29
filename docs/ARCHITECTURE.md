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
- `players.py`: player CRUD and profile loading
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
- `players.py`
  - mixed module: player repository operations and in-memory `SessionStats`.
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
   - loads players through `load_players(db_path)`;
   - creates a default player through `get_or_create_player(...)` when needed.
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
  - `players.py` now has its domain models extracted, but still mixes repository functions and session-only in-memory state;
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

`players.py` currently contains three direct responsibility slices plus imported domain models:

1. repository row-mapping helper
   - `_row_to_aggregate_stats(...)`
2. repository API over `players` / `player_stats`
   - `load_players(...)`
   - `create_player(...)`
   - `delete_player(...)`
   - `get_player_by_name(...)`
   - `get_or_create_player(...)`
3. runtime-only session state
   - `SessionStats`

The pure player models now live separately in `domain/player_models.py`.

This means the file is still mixed, but the cleanest domain-model slice has already been removed. What remains is:

- repository code
- repository convenience bootstrap
- runtime in-memory state

Dependency pressure inside the project:

- `session_controller.py` depends on:
  - `PlayerProfile`
  - `SessionStats`
  - all major player CRUD/bootstrap functions
- `maze_game.py` depends on:
  - `SessionStats` only
- `state_machine/player_select_state.py` and `state_machine/multiplayer_setup_state.py` depend on:
  - `PlayerProfile` for local typed player lists
- `highscore_adapter.py` depends on:
  - `get_or_create_player(...)`

The next clean future cut is:

- move repository functions plus row-mapping helper together;
- move `SessionStats` separately only after call sites are narrowed, because it currently bridges standalone gameplay and `GameSessionController`.

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
  `db_manager.py`, `players.py`, `session_controller.py`, `leaderboard.py`,
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
- `players.py`: player repository functions and in-memory `SessionStats`
- `session_controller.py`: current session coordination plus SQLite run recording
- `leaderboard.py`: leaderboard queries
- `highscores.py`: legacy JSON highscore read/write
- `highscore_adapter.py`: one-time migration bridge

### Testing

- `tests/`: focused unit tests for pure logic extracted from runtime-heavy modules

## Coupling map

Main dependency spine:

- `game_app.py` -> `state_machine/*`
- `game_app.py` -> `session_controller.py`
- `game_app.py` -> `maze_game.py`
- `maze_game.py` -> gameplay helpers (`coins`, `enemies`, `blocks`, `ui`, `sounds`, `sprites`, `maze_gen`)
- `maze_game.py` -> `session_controller.py`
- `session_controller.py` -> `players.py`, `db_manager.py`
- `players.py` -> `db_manager.py`
- `leaderboard.py` -> `db_manager.py`
- `state_machine/leaderboard_state.py` -> `leaderboard.py`

Notable dependency smell:

- `maze_game.py` still remains the main gameplay concentration point, but pure formatting/scoring logic has been extracted into `gameplay/` to reduce incidental coupling.
- `ui.py` is shared by both gameplay runtime and state-machine screens, so presentation concerns are still centralized in one broad helper module.
- `players.py` now delegates domain dataclasses to `domain.player_models`, but still mixes repository-style DB access with session aggregate logic.
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
