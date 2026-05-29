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
4. pygame presentation/media helpers
5. persistence and migration modules

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

## Module responsibilities

### Architectural categories

- Runtime orchestration:
  `game_app.py`, `maze_game.py`
- State machine:
  `state_machine/state_base.py`, `state_machine/main_menu.py`,
  `state_machine/player_select_state.py`, `state_machine/mode_select_state.py`,
  `state_machine/multiplayer_setup_state.py`, `state_machine/leaderboard_state.py`
- Gameplay/domain:
  `maze_gen.py`, `grid_utils.py`, `enemies.py`, `gameplay/*`
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
- `gameplay/result_text.py`: pure end-screen text builders used by gameplay summary rendering
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
- `ui.py`: text rendering and pause/end overlays

### Data/persistence

- `db_manager.py`: SQLite schema and connection setup
- `players.py`: player persistence, aggregate models, and in-memory `SessionStats`
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
- `players.py` mixes repository-style DB access with domain dataclasses and session aggregate logic.
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
