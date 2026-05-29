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
- `persistence/run_repository.py`: completed-run writes and aggregate updates
- `runtime/run_persistence.py`: end-of-run persistence handoff branching
- `runtime/session_stats.py`: in-memory `SessionStats`
- `session_controller.py`: in-memory session plus run recording
- `leaderboard.py`: read queries for leaderboard screens

Flow:

1. `game_app.init_environment()` calls `init_db(db_path)`
2. `GameSessionController.from_db(...)` loads or creates players
3. At end of a run, `maze_game.play_maze()` creates `RunResult`
4. `session_controller.record_run(...)` updates:
   - in-memory `SessionStats`
   - delegates SQL writes to `persistence.run_repository`
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
- `persistence/run_repository.py`
  - dedicated completed-run write path over SQLite, including `runs` insert and `player_stats` aggregate updates.
- `runtime/session_stats.py`
  - isolated runtime-only `SessionStats`.
- `session_controller.py`
  - session orchestration plus runtime/session-state ownership for completed runs.
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
   - delegates persistence branching to `runtime.run_persistence.handle_run_persistence(...)`;
   - inside that helper:
     - updates legacy JSON highscores through `update_highscore_if_better(...)`, `save_highscore(...)`;
     - updates in-memory session stats directly through `SessionStats.add_result(...)` when no controller is present;
     - otherwise creates `RunResult` and calls `session_controller.record_run(...)`.
5. `GameSessionController.record_run(...)`:
   - updates in-memory `SessionStats`;
   - delegates completed-run persistence to `persistence.run_repository.write_completed_run(...)`.

### Responsibility boundary assessment

- `db_manager.py` is a clean infrastructure boundary.
- `leaderboard.py` is a clean read-model/query boundary.
- `highscores.py` is internally coherent, but it keeps a second active persistence path alive.
- `highscore_adapter.py` is coherent as a migration module, but it encodes transitional persistence policy.
- `session_controller.py` remains the main persistence-boundary problem:
  - `players.py` is no longer needed by the production import graph;
  - `session_controller.py` still mixes application/session orchestration with persistence-boundary calls.

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

### Compatibility cleanup result

The old `players.py` compatibility layer is no longer needed by production code.

Current direct owners are now explicit:

- `domain.player_models.py`
  - `PlayerProfile`, `PlayerAggregateStats`
- `runtime.session_stats.py`
  - `SessionStats`
- `persistence.player_repository.py`
  - player CRUD/profile-loading API

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

Placement options considered during the analysis:

- Keep in a legacy root compatibility module
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
  `db_manager.py`, `persistence/player_repository.py`, `session_controller.py`, `leaderboard.py`,
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
- `persistence/run_repository.py`: run-history insert and `player_stats` aggregate updates
- `runtime/session_stats.py`: in-memory session aggregate
- `session_controller.py`: current session coordination plus run-recording orchestration
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
- `session_controller.py` -> `persistence/run_repository.py`
- `persistence/player_repository.py` -> `db_manager.py`
- `leaderboard.py` -> `db_manager.py`
- `state_machine/leaderboard_state.py` -> `leaderboard.py`

Notable dependency smell:

- `maze_game.py` still remains the main gameplay concentration point, but pure formatting/scoring logic has been extracted into `gameplay/` to reduce incidental coupling.
- `ui.py` is shared by both gameplay runtime and state-machine screens, so presentation concerns are still centralized in one broad helper module.
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
   - delegates one completed-run write transaction to `persistence.run_repository`

### What `record_run(...)` mixes after extraction

- runtime/application orchestration
  - obtains per-player session aggregate
  - applies one completed-run result to in-memory state
- repository delegation
  - hands the SQL write path to `persistence.run_repository`

### Best current extraction boundary

Completed in the current code:

- `GameSessionController` remains the orchestration owner;
- raw SQL write details now live in `persistence.run_repository`.

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

This now keeps:

- runtime/session ownership in `GameSessionController`
- persistence write details in a dedicated persistence module

without changing the public gameplay flow or inventing a wider abstraction than the current code needs.

## Gameplay Persistence Boundary Analysis

### Current end-of-run persistence flow

At the end of a run, `maze_game.play_maze(...)` now owns a narrower runtime/persistence edge:

1. prepare end-of-run runtime values:
   - `elapsed_ms`
   - `time_str`
   - `score`
   - per-run coin totals and rarity counters
2. delegate persistence branching to `runtime.run_persistence.handle_run_persistence(...)`
   - legacy JSON highscore update
   - standalone `SessionStats.add_result(...)`
   - controller-present `RunResult` creation
   - controller-present `session_controller.record_run(...)`
4. prepare end-screen summary values
5. show blocking end-screen UI and wait for the next action

### Responsibility zones inside the current end-of-run block

- score/value preparation
  - should stay near gameplay runtime
  - reason:
    values are derived directly from local run state
  - move risk:
    low, and mostly already handled via `gameplay/scoring.py` and `gameplay/result_text.py`

- legacy JSON highscore path
  - now lives behind the runtime handoff helper
  - reason:
    it is persistence policy, not run simulation
  - move risk:
    medium, because behavior is user-visible and still active

- standalone runtime aggregate update
  - now lives behind the runtime handoff helper
  - partly belongs to gameplay runtime because controller-free mode is a real code path
  - move risk:
    medium, because removing it changes the no-controller contract

- persistence orchestration handoff
  - no longer needs to be owned directly by the main end-of-run branch in `maze_game.py`
  - current evidence:
    gameplay now delegates the branching to a runtime helper instead of owning it inline
  - move risk:
    reduced to low-medium for future follow-up

- end-screen UI
  - should remain in `maze_game.py` for now
  - reason:
    it is tightly coupled to the nested pygame loop and return-code contract
  - move risk:
    high

### Option assessment

- Option A: keep the block as-is
  - pluses:
    lowest immediate risk
    no new boundary decisions
  - minuses:
    gameplay runtime keeps knowledge of both JSON and SQLite save paths
    persistence branching remains embedded in end-of-run UI flow
  - risk:
    low now, medium later

- Option B: extract a narrow persistence handoff helper
  - status:
    completed
  - result:
    JSON update + controller/standalone branching now live in `runtime.run_persistence`

- Option C: extract a broader end-of-run coordinator
  - pluses:
    could hide score finalization, persistence branching, and summary preparation together
  - minuses:
    too broad for the current file shape
    risks mixing runtime UI flow with persistence orchestration in a new abstraction
  - risk:
    medium to high

### `highscore.json` interpretation

From the current code:

- it is not only archival;
- it is not only a startup migration source;
- it is still an active runtime sink because gameplay writes it after runs;
- it is also a transitional artifact because SQLite has already become the primary structured store.

Best current description:

- active compatibility output
- transitional persistence artifact

It is no longer the only persistence source, but it is still part of live gameplay save behavior.

### Recommended next Stage 4 code-pass

Option B is now completed.

The next useful Stage 4 decision is narrower:

- keep score preparation in `maze_game.py`;
- keep end-screen UI flow in `maze_game.py`;
- do not widen the helper into a broad end-of-run coordinator yet;
- focus next on policy clarification around `highscore.json` ownership or on any smaller remaining persistence-knowledge slice that can be moved without touching UI flow.

## Legacy Highscore Ownership Analysis

### Current `highscore.json` flow

Actual code paths today:

1. startup migration path
   - `game_app.init_environment()`
   - `highscore_adapter.migrate_highscore_if_needed(...)`
   - `highscore_adapter` loads `highscore.json` through `highscores.load_highscore(...)`
   - if non-empty and not yet migrated, data is copied into SQLite and a `meta` flag is written
2. runtime gameplay path
   - `maze_game.py` loads `Highscore` once at gameplay start
   - end-of-run persistence handoff in `runtime.run_persistence.handle_run_persistence(...)`:
     - calls `update_highscore_if_better(...)`
     - calls `save_highscore(...)` on change
3. after migration
   - migration does not disable runtime JSON writes
   - gameplay continues updating `highscore.json`
   - leaderboard and player/session reads come from SQLite, not from JSON

### What is unique to JSON today

Only the file itself is unique, not the record categories:

- `best_score`
- `max_coins_value`
- `best_time_ms`
- `bronze_max`
- `silver_max`
- `gold_max`
- `diamond_max`

These categories also exist in SQLite, but not with identical ownership semantics:

- JSON is one global record snapshot
- SQLite is player-scoped and run-scoped

So the unique part is:

- one global legacy-format snapshot file
- still maintained during runtime for compatibility reasons

### Actual status of `highscore.json`

By code, it is not:

- the authoritative source of truth for the app overall
- the only runtime store
- a purely archival format

By code, it is:

- an active runtime store for one legacy global highscore snapshot
- a compatibility output
- a transitional persistence artifact
- a startup migration source until the migration flag is set

### Risk of removing runtime writes

What would likely not break immediately:

- SQLite-backed player loading
- SQLite-backed run recording
- leaderboard reads
- `GameSessionController`
- `SessionStats`

What would change:

- `highscore.json` would stop reflecting new runs after gameplay
- any external/manual workflow relying on that file would become stale
- startup migration for future fresh DBs would only see old JSON state unless export behavior remains

Current runtime consumers besides the gameplay update path:

- no in-app runtime reader uses `highscore.json` after gameplay starts
- `highscore_adapter.py` reads it only during startup migration

### Policy options

- Option A: keep JSON permanently as a second persistence path
  - pluses:
    minimal product risk
    preserves backward-compatible file behavior
  - minuses:
    permanent dual-write complexity
    persistence ownership stays conceptually split
  - risk:
    low short-term, medium long-term
  - future change size:
    small now, ongoing maintenance cost later

- Option B: keep JSON as compatibility export only
  - pluses:
    moves the project toward SQLite ownership while preserving optional legacy file output
    can decouple gameplay runtime from direct JSON policy over time
  - minuses:
    requires deciding when export happens and what contract it serves
    still keeps format compatibility obligations
  - risk:
    medium
  - future change size:
    medium, several narrow steps

- Option C: make SQLite the only source of truth and remove runtime JSON writes entirely
  - pluses:
    cleanest persistence model
    removes dual-write behavior
  - minuses:
    highest compatibility risk
    breaks any workflow expecting a live `highscore.json`
    requires explicit migration/export story first
  - risk:
    medium to high
  - future change size:
    medium

### Recommended direction

Recommend Option B.

Reason:

- SQLite is already the structured store the app really uses for players, runs, and leaderboard data;
- `highscore.json` still behaves like a compatibility side-path, not like the main source of truth;
- Option B keeps the project honest about that role without forcing a sudden compatibility break.

### Safe staged plan

- Step 4B
  - document the exact compatibility contract for `highscore.json`
  - decide whether export is required on every completed run or can move to a narrower boundary
  - risk:
    low

- Step 4C
  - introduce a narrow export-oriented boundary for legacy highscore writes without changing file format
  - keep behavior the same first
  - risk:
    medium

- Step 4D
  - only after the contract is explicit, decide whether runtime writes stay as compatibility export or can be removed in favor of SQLite-only ownership
  - risk:
    medium to high, because this is the first user-visible policy step
