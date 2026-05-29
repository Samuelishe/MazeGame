# Modules Map

## Purpose

This document is the file-level architecture map for Maze Game.

It describes:

- what each Python module currently does;
- which layer it belongs to;
- who depends on it;
- where it would fit better in a future directory structure;
- what architectural issues are visible from the current module graph.

This is an inspection document only. It does not imply any immediate file moves.

## Layer map

### App shell / runtime orchestration

- `game_app.py`
- `maze_game.py`
- `runtime/session_stats.py`
- `runtime/run_persistence.py`

### State machine / screen flow

- `state_machine/state_base.py`
- `state_machine/main_menu.py`
- `state_machine/player_select_state.py`
- `state_machine/mode_select_state.py`
- `state_machine/multiplayer_setup_state.py`
- `state_machine/leaderboard_state.py`

### Gameplay domain and gameplay support

- `domain/player_models.py`
- `maze_gen.py`
- `grid_utils.py`
- `enemies.py`
- `coins.py`
- `blocks.py`
- `effects.py`
- `palette.py`
- `gameplay/formatting.py`
- `gameplay/maze_positions.py`
- `gameplay/scoring.py`
- `gameplay/result_text.py`
- `gameplay/hud_text.py`

### Presentation / media / pygame-facing helpers

- `presentation/__init__.py`
- `presentation/coin_rendering.py`
- `presentation/block_rendering.py`
- `presentation/enemy_sprites.py`
- `ui.py`
- `sounds.py`
- `sprites.py`

### Persistence / session / leaderboard data

- `persistence/player_repository.py`
- `persistence/run_repository.py`
- `db_manager.py`
- `session_controller.py`
- `leaderboard.py`
- `highscores.py`
- `highscore_adapter.py`

### Tests

- `tests/test_formatting.py`
- `tests/test_maze_positions.py`
- `tests/test_scoring.py`
- `tests/test_scoring_preparation.py`
- `tests/test_result_text.py`
- `tests/test_hud_text.py`
- `tests/test_player_repository.py`
- `tests/test_session_controller_record_run.py`
- `tests/test_session_stats.py`
- `tests/test_run_persistence.py`

## Module catalogue

### `domain/player_models.py`

- Role:
  pure player domain models.
- Main classes:
  `PlayerAggregateStats`, `PlayerProfile`.
- Main functions:
  none.
- Used by:
  `session_controller.py`, `state_machine/player_select_state.py`, `state_machine/multiplayer_setup_state.py`.
- Depends on:
  stdlib only.
- Future fit:
  keep in `domain/`.
- Notes:
  first safe Stage 4 split from `players.py`; this module contains no repository or runtime-session behavior.

### `persistence/player_repository.py`

- Role:
  SQLite-backed player repository API.
- Main classes:
  none.
- Main functions:
  `load_players`, `create_player`, `delete_player`, `get_player_by_name`, `get_or_create_player`.
- Used by:
  `session_controller.py`, `highscore_adapter.py`.
- Depends on:
  `db_manager`, `domain.player_models`.
- Future fit:
  keep in `persistence/`.
- Notes:
  owns player CRUD/profile-loading after Stage 4 Step 1B; bootstrap-sensitive behavior stays unchanged and now has minimal disposable-DB smoke coverage.

### `runtime/session_stats.py`

- Role:
  runtime-only in-memory per-session aggregate state.
- Main classes:
  `SessionStats`.
- Main functions:
  none beyond methods on `SessionStats`.
- Used by:
  `maze_game.py`, `session_controller.py`, tests.
- Depends on:
  stdlib only.
- Future fit:
  keep in `runtime/`.
- Notes:
  Stage 4 Step 1C moved `SessionStats` here as the first explicit runtime-oriented boundary step; no broader runtime package migration has started.

### `runtime/run_persistence.py`

- Role:
  runtime-facing end-of-run persistence handoff helper.
- Main classes:
  none.
- Main functions:
  `handle_run_persistence`.
- Used by:
  `maze_game.py`, tests.
- Depends on:
  `highscores`, `session_controller.RunResult`.
- Future fit:
  keep in `runtime/`.
- Notes:
  owns JSON highscore update plus standalone/controller result-recording branching without taking over score calculation, UI, or raw SQLite writes.

### `presentation/coin_rendering.py`

- Role:
  pygame-facing coin rendering helpers.
- Main classes:
  none.
- Main functions:
  `draw_coin`.
- Used by:
  `maze_game.py`.
- Depends on:
  `pygame`, `coins`.
- Future fit:
  keep in `presentation/`.
- Notes:
  Stage 3 Step 2 extracted the coin draw path here without changing coin spawn/data ownership.

### `presentation/__init__.py`

- Role:
  package marker for narrow pygame-facing presentation helpers.
- Main classes:
  none.
- Main functions:
  none.
- Used by:
  import system only.
- Depends on:
  none.
- Future fit:
  keep as package marker.
- Notes:
  introduced in Stage 3 Step 2 as the first explicit `presentation/` boundary.

### `presentation/block_rendering.py`

- Role:
  pygame-facing temporary block rendering helpers.
- Main classes:
  none.
- Main functions:
  `draw_block_cell`.
- Used by:
  `maze_game.py`.
- Depends on:
  `pygame`, stdlib only.
- Future fit:
  keep in `presentation/`.
- Notes:
  Stage 3 Step 2 extracted the block draw path here without changing block spawn/respawn ownership.

### `presentation/enemy_sprites.py`

- Role:
  pygame-facing enemy sprite-sheet loading and `EnemyType` mapping helpers.
- Main classes:
  none.
- Main functions:
  `load_enemy_sheets_by_type`.
- Used by:
  `maze_game.py`.
- Depends on:
  `pygame`, `enemies`, `sprites`.
- Future fit:
  keep in `presentation/`.
- Notes:
  Stage 3 Step 4 extracted enemy asset paths, sheet loading, fallback-to-red behavior, and type mapping here without moving runtime animation setup.

### `persistence/run_repository.py`

- Role:
  SQLite-backed completed-run write boundary.
- Main classes:
  none.
- Main functions:
  `write_completed_run`.
- Used by:
  `session_controller.py`.
- Depends on:
  `db_manager`.
- Future fit:
  keep in `persistence/`.
- Notes:
  owns the former `record_run(...)` raw SQL path: `runs` insert, `player_stats` aggregate update, win-only `best_time_ms` policy, and connection/cursor lifecycle.

### `game_app.py`

- Role:
  app bootstrap, pygame lifecycle start, DB init, migration trigger, FSM wiring, gameplay handoff.
- Main classes:
  `GameplayWrapper`.
- Main functions:
  `init_environment`, `make_main_menu`, `show_*`, `run_game_app`, `quit_game`.
- Used by:
  process entrypoint only.
- Depends on:
  `state_machine/*`, `session_controller`, `db_manager`, `highscore_adapter`, `maze_game`.
- Future fit:
  `runtime/app.py` or `app_shell/app.py`.
- Notes:
  runtime orchestration and menu composition are mixed in one root module.

### `maze_game.py`

- Role:
  main gameplay runtime loop and the largest behavior host in the project.
- Main classes:
  none.
- Main functions:
  `compute_window_size`, `sample_coins_count`, `play_maze`, plus small local gameplay helpers.
- Used by:
  `game_app.py`.
- Depends on:
  `coins`, `effects`, `gameplay/*`, `highscores`, `sounds`, `sprites`, `runtime.session_stats`, `grid_utils`, `enemies`, `blocks`, `palette`, `ui`, `maze_gen`, `session_controller`.
- Future fit:
  split gradually across `runtime/gameplay_loop.py`, `runtime/gameplay_rendering.py`, `runtime/gameplay_flow.py`, while keeping root file as migration shell until stable.
- Notes:
  dominant god module; mixes gameplay rules, state mutation, rendering, pause/end overlays, persistence hooks, audio, assets, and level control.

#### `maze_game.py` internal zones

Approximate size: 799 lines total.

- Lines `1-66`: stale module docstring and imports
  - responsibility:
    file header plus all external imports.
  - coupling:
    very high import fan-in.
  - external dependencies:
    14 project modules plus stdlib.
  - extraction risk:
    none as analysis, but the stale docstring is a maintenance smell.

- Lines `68-75`: shared type alias and constants
  - responsibility:
    `Coord`, `MAZE_GRID_ROWS`, `MAZE_GRID_COLS`, `MAZE_CELL_PX`.
  - coupling:
    low.
  - external dependencies:
    typing only.
  - extraction risk:
    low, but not urgent.

- Lines `78-154`: top-level helpers
  - responsibility:
    `compute_window_size`, passability helpers, coin-count sampling.
  - coupling:
    low to medium.
  - external dependencies:
    `grid_utils`, `random`.
  - extraction risk:
    low.

- Lines `156-216`: `play_maze()` entry and session-level setup
  - responsibility:
    session/player resolution, local stats fallback, sound/effects/highscore initialization.
  - coupling:
    medium to high.
  - external dependencies:
    `SessionStats`, `SoundBank`, `Effects`, `highscores`, `session_controller`.
  - extraction risk:
    medium.

- Lines `218-903`: `run_once()` nested runtime host
  - responsibility:
    one full round from maze entry setup through end-screen return code.
  - coupling:
    very high.
  - external dependencies:
    nearly every runtime-facing dependency in the file.
  - extraction risk:
    high unless split by narrow internal clusters.

- Lines `228-240`: entry/exit border translation
  - responsibility:
    convert border cells to inner player/goal start cells.
  - coupling:
    low.
  - external dependencies:
    none beyond local values.
  - extraction risk:
    low.

- Lines `243-311`: enemy sprite asset loading and sprite-type mapping
  - responsibility:
    load enemy sheets from disk, fallback if missing, map sheets to `EnemyType`.
  - coupling:
    medium.
  - external dependencies:
    `pygame`, `SpriteSheet`, `EnemyType`.
  - extraction risk:
    medium, because it is pygame- and asset-path-dependent but behaviorally isolated.

#### Enemy asset loading boundary analysis

Current asset-loading path:

- asset path definition
  - four hardcoded files:
    - `resources/images/enemies/Tiny_Slime Red.png`
    - `resources/images/enemies/Tiny_Slime Green.png`
    - `resources/images/enemies/Tiny_Slime Purple.png`
    - `resources/images/enemies/Tiny_Slime Yellow.png`
- sprite loading
  - `SpriteSheet.from_file(...)` with:
    - `frame_size=(16, 16)`
    - `spacing=(8, 8)`
    - `margin=(4, 4)`
- fallback behavior
  - load loop skips missing files via `except pygame.error`
  - if nothing loaded at all, force-load `Tiny_Slime Red.png`
- type mapping
  - local `sheet_or_default(...)`
  - local `enemy_sheets_by_type: dict[EnemyType, list[SpriteSheet]]`
- runtime usage after loading
  - `maze_game.py` later chooses a sheet per enemy from `enemy_sheets_by_type`
  - then creates `AnimatedSprite(...)`
  - then shifts `anim.start_time` for desynchronization

Responsibility split:

- asset path definition:
  presentation concern
- `SpriteSheet.from_file(...)` calls:
  presentation concern
- missing-asset fallback:
  mixed concern, because it is asset-loading policy but affects runtime resilience
- `EnemyType -> SpriteSheet` mapping:
  presentation concern with light design semantics
- `AnimatedSprite(...)` creation and per-enemy randomization:
  runtime concern

Recommended narrow future split:

- completed:
  - asset path definition
  - `SpriteSheet.from_file(...)` loop
  - `sheet_or_default(...)`
  - `enemy_sheets_by_type` construction
  moved to `presentation.enemy_sprites`
- kept in `maze_game.py`:
  - per-enemy `AnimatedSprite(...)` creation
  - `anim.start_time` staggering
  - all enemy spawn/runtime behavior

- Lines `314-396`: HUD font setup and local mixed-text rendering integration
  - responsibility:
    create HUD fonts and integrate mixed text rendering into one surface.
  - coupling:
    medium.
  - external dependencies:
    `pygame`, `ui` font helpers and `ui.render_mixed_text`.
  - extraction risk:
    low to medium.

- Lines `398-500`: runtime entity spawning and initial state setup
  - responsibility:
    safe zones, enemy spawn selection, enemy animation setup, block spawn, coin spawn, counters, timers, flags.
  - coupling:
    high.
  - external dependencies:
    `enemies`, `blocks`, `coins`, `sprites`, `palette`, `pygame`, `random`.
  - extraction risk:
    medium.

- Lines `501-524`: `try_collect_at()`
  - responsibility:
    coin pickup handling, rarity counters, sound triggers, coin flash trigger, list mutation.
  - coupling:
    medium to high.
  - external dependencies:
    `CoinRarity`, `SoundBank`, `Effects`.
  - extraction risk:
    medium.

- Lines `526-592`: event processing and pause control flow
  - responsibility:
    QUIT, ESC pause menu, manual movement, KEYUP direction reset.
  - coupling:
    very high.
  - external dependencies:
    `pygame`, `ui` pause helpers, mutable timing state.
  - extraction risk:
    high.

- Lines `594-605`: auto-movement tick
  - responsibility:
    continue player motion while key direction is held.
  - coupling:
    high.
  - external dependencies:
    local mutable runtime state and `try_collect_at()`.
  - extraction risk:
    medium.

- Lines `607-652`: enemy processing
  - responsibility:
    enemy AI step invocation, movement validation, oscillation update, step timing.
  - coupling:
    medium to high.
  - external dependencies:
    `enemies` runtime objects, local maze/player/blocked state.
  - extraction risk:
    medium.

- Lines `654-669`: block timer processing
  - responsibility:
    blocked set refresh, timed block respawn, forbidden-cell recomputation.
  - coupling:
    medium.
  - external dependencies:
    `blocks`, local enemy/player/goal state.
  - extraction risk:
    medium.

- Lines `671-677`: collision resolution
  - responsibility:
    detect player-enemy overlap and trigger defeat sound.
  - coupling:
    low to medium.
  - external dependencies:
    `SoundBank`, local state.
  - extraction risk:
    low to medium.

- Lines `679-746`: world rendering
  - responsibility:
    maze background, blocks, coins, goal, trail, enemies, player, effects.
  - coupling:
    very high to pygame presentation, low to persistence.
  - external dependencies:
    `pygame`, `blocks`, `coins`, `sprites`, `effects`.
  - extraction risk:
    medium.

- Lines `748-784`: HUD rendering
  - responsibility:
    build HUD text, render mixed HUD surface, build background surface, blit HUD.
  - coupling:
    medium.
  - external dependencies:
    `gameplay.hud_text`, `pygame`, local HUD renderer.
  - extraction risk:
    low to medium.

- Lines `786-897`: score processing, persistence hooks, end-screen summary, end-menu control flow
  - responsibility:
    compute elapsed time, score params, final score, JSON highscore update, session/SQLite record, summary text, end overlay, blocking choice wait.
  - coupling:
    very high.
  - external dependencies:
    `gameplay.formatting`, `gameplay.scoring`, `gameplay.result_text`, `highscores`, `session_controller`, `runtime.session_stats.SessionStats`, `ui`, `pygame`.
  - extraction risk:
    high as one block; medium if split into value preparation vs UI wait.

#### `maze_game.py` gameplay persistence boundary

Current end-of-run persistence knowledge that still lives in `maze_game.py`:

- update `highscore.json` through `highscores.py`;
- choose between standalone `SessionStats` recording and controller-present recording;
- construct `RunResult`;
- call `session_controller.record_run(...)`.

What already moved out:

- score-input preparation -> `gameplay/scoring.py`
- end-summary value preparation -> `gameplay/result_text.py`
- raw SQLite write path -> `persistence.run_repository.py` through `session_controller.py`

What still looks like the next useful boundary:

- a narrow persistence handoff helper for:
  - JSON highscore update
  - standalone `SessionStats.add_result(...)`
  - `RunResult` creation
  - `session_controller.record_run(...)` call

Why not broader yet:

- the same block still touches blocking end-screen UI and live runtime locals;
- a full end-of-run coordinator would be wider than the current evidence justifies.

- Lines `907-933`: outer replay/new-level wrapper
  - responsibility:
    repeat `run_once()`, return early for multiplayer, internal single-player restart/new-level handling.
  - coupling:
    medium.
  - external dependencies:
    `RoundMode`, `maze_gen`.
  - extraction risk:
    medium.

#### `maze_game.py` extraction candidates

Priority A: very safe

- HUD mixed-text renderer from lines `355-396`
  - pygame dependency:
    yes.
  - runtime-state dependency:
    low.
  - behavior-safe extraction:
    yes, if signature stays explicit and rendering order is preserved.

Priority B: medium risk

- enemy sprite loading and per-type mapping from lines `253-311`
  - pygame dependency:
    yes.
  - runtime-state dependency:
    low.
  - behavior-safe extraction:
    likely yes.

- runtime spawn/setup block from lines `398-500`
  - pygame dependency:
    indirect via timing and later animation usage.
  - runtime-state dependency:
    high.
  - behavior-safe extraction:
    possible, but should stay extract-only and explicit.

- coin collection handler from lines `501-524`
  - pygame dependency:
    indirect through sound/effects only.
  - runtime-state dependency:
    medium to high due to list and counter mutation.
  - behavior-safe extraction:
    possible with explicit mutable arguments.

- player auto-movement and enemy/block/collision update slices from lines `594-677`
  - pygame dependency:
    no direct rendering dependency.
  - runtime-state dependency:
    high.
  - behavior-safe extraction:
    possible, but requires careful argument shaping.

- world rendering block from lines `679-746`
  - pygame dependency:
    yes.
  - runtime-state dependency:
    medium.
  - behavior-safe extraction:
    possible as a dedicated render helper.

Priority C: high risk

- pause event flow from lines `526-566`
  - pygame dependency:
    yes.
  - runtime-state dependency:
    very high.
  - behavior-safe extraction:
    risky due to timing offsets and blocking UI flow.

- full event handling block from lines `526-592`
  - pygame dependency:
    yes.
  - runtime-state dependency:
    very high.
  - behavior-safe extraction:
    risky.

- full score/persistence/end-screen block from lines `786-897` as one unit
  - pygame dependency:
    partly.
  - runtime-state dependency:
    very high.
  - behavior-safe extraction:
    risky unless split first into value prep vs UI wait.

- `run_once()` as a whole
  - pygame dependency:
    yes.
  - runtime-state dependency:
    maximal.
  - behavior-safe extraction:
    not a good near-term target.

### `session_controller.py`

- Role:
  session state, player rotation modes, in-memory session stats, SQLite run recording.
- Main classes:
  `RoundMode`, `RunResult`, `GameSessionController`.
- Main functions:
  class methods and record/update methods inside `GameSessionController`.
- Used by:
  `game_app.py`, `maze_game.py`, `state_machine/player_select_state.py`, `state_machine/mode_select_state.py`, `state_machine/multiplayer_setup_state.py`, `state_machine/leaderboard_state.py`.
- Depends on:
  `db_manager`, `persistence.player_repository`, `persistence.run_repository`, `runtime.session_stats`.
- Future fit:
  `persistence/session_controller.py` or `application/session_controller.py`.
- Notes:
  not a gameplay module, but still broad because it combines session coordination, player rotation policy, and run-recording orchestration; raw SQL write ownership has now moved to `persistence/run_repository.py`.

### `db_manager.py`

- Role:
  SQLite connection setup, PRAGMA management, schema bootstrap, meta flags.
- Main classes:
  none.
- Main functions:
  `get_connection`, `init_db`, `set_meta_flag`, `get_meta_flag`.
- Used by:
  `game_app.py`, `session_controller.py`, `leaderboard.py`, `highscore_adapter.py`.
- Depends on:
  stdlib only.
- Future fit:
  `infrastructure/db_manager.py`.
- Notes:
  clean infrastructure module; root placement is the main issue, not internal design.

#### `SessionStats` analysis

- Current direct usage map:
  - `session_controller.py`
    - `GameSessionController.session_stats_by_player`:
      in-memory storage keyed by `player_id`
      usage type: read/write
      dependency strength: high
    - `GameSessionController.__post_init__()`:
      creates missing `SessionStats()` objects
      usage type: write
      dependency strength: high
    - `GameSessionController.create_player(...)`:
      initializes `SessionStats()` for a new player
      usage type: write
      dependency strength: high
    - `GameSessionController.delete_player_from_session(...)`:
      removes cached `SessionStats` for deleted player
      usage type: write
      dependency strength: medium
    - `GameSessionController.configure_rotation_players(...)`:
      filters and backfills `SessionStats` entries
      usage type: read/write
      dependency strength: high
    - `GameSessionController.get_session_stats_for(...)`:
      lookup-or-create accessor
      usage type: read/write
      dependency strength: high
    - `GameSessionController.record_run(...)`:
      updates counters through `stats.add_result(...)`
      usage type: write
      dependency strength: high
  - `maze_game.py`
    - `play_maze(...)` bootstrap:
      if controller exists, reads `session_controller.get_session_stats_for(...)`;
      otherwise constructs standalone `SessionStats()`
      usage type: read/write
      dependency strength: high
    - `play_maze(...)` end-of-run flow:
      standalone mode calls `stats.add_result(...)`
      usage type: write
      dependency strength: high
    - `play_maze(...)` end-of-run summary:
      reads `stats.summary_line()`
      usage type: read
      dependency strength: medium
- Indirect/non-usage:
  - `game_app.py`, `leaderboard.py`, `highscore_adapter.py`, and `state_machine/*` do not import `SessionStats` directly.
- Responsibility classification:
  - not a persistence model;
  - not a service object;
  - best described as runtime session state and session aggregate object.
- Dependency facts:
  - imports: stdlib `dataclasses` only;
  - uses no project models directly;
  - does not depend on SQLite;
  - does not depend on pygame;
  - does not depend on `PlayerProfile`.
- Placement options:
  - Option A: keep in a legacy root compatibility module
    - pluses:
      zero import churn
      keeps current code stable
    - minuses:
      misleading ownership next to legacy compatibility re-export
      keeps runtime state attached to a persistence-flavored root module
    - risk:
      low short-term, higher long-term documentation drift
  - Option B: move to `domain/`
    - pluses:
      pure dataclass can live in a non-pygame package
      removes the last real state object from the old root compatibility area
    - minuses:
      this object is not a stable game-domain concept; it is session-lifetime cache/aggregate
      `domain/` currently hosts durable models and pure rules, which is a weaker fit
    - risk:
      medium due to semantic mismatch
  - Option C: move to `runtime/` or `application/`-style runtime package
    - pluses:
      matches actual usage: session-lifetime mutable state for active process only
      separates runtime/session concerns from persistence concerns cleanly
      aligns with `GameSessionController` ownership better than `domain/`
    - minuses:
      no dedicated `runtime/` or `application/` package exists yet, so this introduces a new boundary decision
    - risk:
      medium now, lower after package-boundary prep
- Recommended direction:
  - completed: `SessionStats` now lives in `runtime/session_stats.py`;
  - broader runtime-package migration remains a separate later decision.

### `leaderboard.py`

- Role:
  read-only leaderboard/query API over SQLite.
- Main classes:
  `RunEntry`, `PlayerEntry`.
- Main functions:
  `get_top_scores`, `get_best_times`, `get_top_coins`, `get_players_sorted`, `get_player_aggregate`.
- Used by:
  `state_machine/leaderboard_state.py`.
- Depends on:
  `db_manager`.
- Future fit:
  `persistence/leaderboard_queries.py`.
- Notes:
  mostly clean read-model module; root placement is the main structural issue, not the query API itself.

### `highscores.py`

- Role:
  legacy JSON highscore read/write/update logic.
- Main classes:
  `Highscore`.
- Main functions:
  `default_path`, `load_highscore`, `save_highscore`, `update_highscore_if_better`.
- Used by:
  `maze_game.py`, `highscore_adapter.py`.
- Depends on:
  stdlib only.
- Future fit:
  `persistence/legacy_highscores.py`.
- Notes:
  legacy persistence remains active in runtime, which keeps persistence ownership split.

### `highscore_adapter.py`

- Role:
  one-time migration bridge from `highscore.json` into SQLite.
- Main classes:
  none.
- Main functions:
  `migrate_highscore_if_needed`.
- Used by:
  `game_app.py`.
- Depends on:
  `db_manager`, `highscores`, `players`.
- Future fit:
  `persistence/migrations/highscore_adapter.py`.
- Notes:
  migration logic is cleanly separated, but it documents an unfinished persistence transition.

## Persistence Architecture

### Current flow map

1. `game_app.py`
   - calls `db_manager.init_db(...)`
   - calls `highscore_adapter.migrate_highscore_if_needed(...)`
   - creates `GameSessionController.from_db(...)`
2. `GameSessionController.from_db(...)`
   - reads players via `persistence.player_repository.load_players(...)`
   - may create a default player via `persistence.player_repository.get_or_create_player(...)`
3. `state_machine/player_select_state.py`
   - uses `GameSessionController` to create, delete, choose players
4. `state_machine/multiplayer_setup_state.py`
   - uses `GameSessionController` to create, delete, and configure active player rotation
5. `state_machine/mode_select_state.py`
   - changes `RoundMode` through `GameSessionController`
6. `state_machine/leaderboard_state.py`
   - reads leaderboard data through `leaderboard.get_top_scores(...)` and `leaderboard.get_players_sorted(...)`
7. `maze_game.py`
   - updates legacy JSON highscores through `highscores.py`
   - writes SQLite run data through `session_controller.record_run(...)` when a session controller exists
   - otherwise updates only local in-memory `SessionStats`

### Per-module boundary assessment

- `db_manager.py`
  - domain logic:
    none.
  - persistence logic:
    all of it.
  - mixed incorrectly:
    no.

- `persistence/player_repository.py`
  - domain logic:
    none beyond typed return shapes from `domain.player_models`.
  - persistence logic:
    all of it.
  - mixed incorrectly:
    no; this is now the dedicated player CRUD/profile-loading slice.

- `session_controller.py`
  - domain logic:
    `RoundMode`, `RunResult`, current-player rotation policy.
  - persistence logic:
    defensive DB init in lifecycle methods, repository delegation for completed-run writes.
  - mixed incorrectly:
    still partially; player/session orchestration remains mixed with persistence-boundary calls, but raw SQL no longer lives here.

- `leaderboard.py`
  - domain logic:
    `RunEntry`, `PlayerEntry` as read-model data shapes.
  - persistence logic:
    all query functions.
  - mixed incorrectly:
    mildly; read models and SQL are together, but the module is still coherent.

- `highscores.py`
  - domain logic:
    `Highscore` data shape and record-improvement rules.
  - persistence logic:
    JSON load/save path.
  - mixed incorrectly:
    moderately; update policy and JSON I/O are in one module, but the larger problem is that this path is still active alongside SQLite.

- `highscore_adapter.py`
  - domain logic:
    migration interpretation rules for legacy highscore data.
  - persistence logic:
    writes migrated data into `player_stats`, `runs`, and `meta`.
  - mixed incorrectly:
    acceptably; it is a transitional migration module by nature.

## Persistence Refactoring Candidates

- `session_controller.py` split candidate
  - target:
    keep session/mode/current-player orchestration separate from SQLite write logic.
  - risk:
    medium.

- `maze_game.py` persistence-boundary narrowing
  - target:
    reduce direct knowledge of both JSON and SQLite save paths in gameplay runtime.
  - risk:
    medium.

- `highscores.py` ownership decision
  - target:
    make runtime legacy JSON support either explicit compatibility mode or eventual archival path.
  - risk:
    medium because save behavior is user-visible.

### `ui.py`

- Role:
  pygame UI helper layer: font loading, mixed emoji/text rendering, pause overlay, end overlay.
- Main classes:
  none.
- Main functions:
  `get_emoji_font`, `get_text_font`, `render_mixed_text`, `draw_end_menu`, `wait_end_choice`, `draw_pause_menu`, `wait_pause_choice`.
- Used by:
  `maze_game.py`, all screen modules under `state_machine/`.
- Depends on:
  `pygame`.
- Future fit:
  split between `presentation/fonts.py`, `presentation/text.py`, `presentation/overlays.py`.
- Notes:
  this is already a presentation module, but it combines reusable text helpers with blocking overlay control flow; `render_mixed_text` is now reused by gameplay HUD rendering as well as overlay text rendering.

### `sounds.py`

- Role:
  audio loading and fallback procedural sound generation.
- Main classes:
  `_ToneSpec`, `SoundBank`.
- Main functions:
  methods inside `SoundBank`.
- Used by:
  `maze_game.py`.
- Depends on:
  `pygame`.
- Future fit:
  `presentation/audio.py`.
- Notes:
  clean support module; tightly pygame-bound by nature.

### `sprites.py`

- Role:
  sprite sheet extraction and animated sprite timing.
- Main classes:
  `SpriteSheet`, `AnimatedSprite`.
- Main functions:
  methods inside the two classes.
- Used by:
  `maze_game.py`.
- Depends on:
  `pygame`.
- Future fit:
  `presentation/sprites.py`.
- Notes:
  clean support module.

### `palette.py`

- Role:
  color palette generation from one seed hue.
- Main classes:
  none.
- Main functions:
  `make_palette`.
- Used by:
  `maze_game.py`.
- Depends on:
  stdlib only.
- Future fit:
  `presentation/palette.py` or `gameplay/visual_palette.py`.
- Notes:
  tiny presentation-oriented module; current root placement is unnecessary, but there is no meaningful domain/rendering split to perform here.

### `effects.py`

- Role:
  lightweight visual effects for gameplay.
- Main classes:
  `CoinFlash`, `Effects`.
- Main functions:
  methods on `Effects`.
- Used by:
  `maze_game.py`.
- Depends on:
  `pygame`.
- Future fit:
  `presentation/effects.py`.
- Notes:
  presentation-only concern; no meaningful domain split is visible in the current code.

### `blocks.py`

- Role:
  temporary blocking wall model plus spawn/respawn behavior.
- Main classes:
  `Block`.
- Main functions:
  `spawn_blocks`, `respawn_block`.
- Used by:
  `maze_game.py`.
- Depends on:
  stdlib.
- Future fit:
  keep as domain/runtime support beside `presentation/block_rendering.py`, or later regroup under a gameplay/domain package.
- Notes:
  Stage 3 Step 2 removed pygame drawing ownership from this module.

#### `blocks.py` responsibility map

- `Block`
  - classification:
    domain/runtime data object
  - used by:
    `maze_game.py`, `spawn_blocks(...)`, `respawn_block(...)`
  - depends on:
    stdlib only
- `spawn_blocks(...)`
  - classification:
    domain/runtime spawn logic
  - used by:
    `maze_game.py`
  - depends on:
    maze layout data, forbidden-cell input, stdlib randomness
- `respawn_block(...)`
  - classification:
    domain/runtime respawn logic
  - used by:
    `maze_game.py`
  - depends on:
    `Block`, maze layout data, forbidden-cell input, stdlib randomness
- `_pulse_color(...)`
  - classification:
    rendering helper
  - used by:
    `presentation.block_rendering.draw_block_cell(...)`
  - depends on:
    stdlib math only
- `draw_block_cell(...)`
  - classification:
    pygame rendering logic
  - used by:
    `maze_game.py` through `presentation.block_rendering`
  - depends on:
    `pygame`, `_pulse_color(...)`

#### `blocks.py` Stage 3 analysis

- Safe future split candidate:
  completed: `_pulse_color(...)` and `draw_block_cell(...)` moved behind `presentation.block_rendering` while keeping `Block`, `spawn_blocks(...)`, and `respawn_block(...)` together.
- Why this is the narrowest useful step:
  rendering has a small explicit API, while spawn/respawn behavior stays tightly coupled to maze data and forbidden-cell rules.
- Risk:
  medium if done narrowly, because `maze_game.py` still owns timing and positioning inputs but the draw path itself is isolated.

### `coins.py`

- Role:
  coin rarity definitions, data, spawn logic, and rarity text helper.
- Main classes:
  `CoinRarity`, `RarityConfig`, `Coin`.
- Main functions:
  `spawn_coins`, `rarity_icon`.
- Used by:
  `maze_game.py`, `gameplay/result_text.py`.
- Depends on:
  stdlib.
- Future fit:
  keep as domain/runtime support beside `presentation/coin_rendering.py`, or later regroup under a gameplay/domain package.
- Notes:
  Stage 3 Step 2 removed pygame drawing ownership from this module.

#### `coins.py` responsibility map

- `CoinRarity`
  - classification:
    domain enum
  - used by:
    `coins.py`, `maze_game.py`, `gameplay/result_text.py`
  - depends on:
    stdlib enum only
- `RarityConfig`
  - classification:
    domain configuration object
  - used by:
    `coins.py`
  - depends on:
    stdlib dataclasses only
- `RARITY_CONFIG`
  - classification:
    domain/static configuration
  - used by:
    spawn and rendering paths inside `coins.py`
  - depends on:
    `CoinRarity`, `RarityConfig`
- `Coin`
  - classification:
    domain/runtime data object
  - used by:
    `maze_game.py`, `spawn_coins(...)`, `draw_coin(...)`
  - depends on:
    `CoinRarity`
- `_choose_rarity(...)`
  - classification:
    domain helper
  - used by:
    `spawn_coins(...)`
  - depends on:
    `RARITY_CONFIG`
- `spawn_coins(...)`
  - classification:
    domain/runtime spawn logic
  - used by:
    `maze_game.py`
  - depends on:
    maze layout data, forbidden-cell input, `Coin`, `CoinRarity`, `RARITY_CONFIG`, stdlib randomness
- `rarity_icon(...)`
  - classification:
    presentation-adjacent text helper
  - used by:
    `maze_game.py`, `gameplay/result_text.py`
  - depends on:
    `CoinRarity`
- `_draw_diamond(...)`
  - classification:
    pygame rendering helper
  - used by:
    `presentation.coin_rendering.draw_coin(...)`
  - depends on:
    `pygame`
- `draw_coin(...)`
  - classification:
    pygame rendering logic
  - used by:
    `maze_game.py` through `presentation.coin_rendering`
  - depends on:
    `pygame`, `RARITY_CONFIG`, `_draw_diamond(...)`

#### `coins.py` Stage 3 analysis

- Safe future split candidate:
  completed: `_draw_diamond(...)` and `draw_coin(...)` moved behind `presentation.coin_rendering`.
- Keep in place for now:
  `CoinRarity`, `RarityConfig`, `RARITY_CONFIG`, `Coin`, `_choose_rarity(...)`, `spawn_coins(...)`, `rarity_icon(...)`.
- Why `rarity_icon(...)` is not grouped with draw helpers:
  it is used by deterministic result-summary text builders and does not depend on `pygame`.
- Risk:
  medium if limited to draw-path extraction, because gameplay spawn rules and HUD/end-summary text can stay untouched.

### `enemies.py`

- Role:
  enemy types, spawn schemes, movement strategies, BFS chase logic, patrol path building, safe zones.
- Main classes:
  `EnemyType`, `EnemyParams`, `Enemy`.
- Main functions:
  `spawn_enemies`, `spawn_enemies_by_scheme`, `choose_enemy_direction`, `build_patrol_path`, `bfs_next_step_towards`, strategy functions, `build_safe_zone`.
- Used by:
  `maze_game.py`.
- Depends on:
  `grid_utils`, stdlib.
- Future fit:
  `domain/enemies.py` or split into `domain/enemy_models.py` and `domain/enemy_ai.py`.
- Notes:
  large but mostly domain-oriented; one of the best candidates for future extraction without touching UX.

### `maze_gen.py`

- Role:
  Wilson spanning tree generation and maze conversion.
- Main classes:
  none.
- Main functions:
  `wilson_grid`, `tree_to_maze`, `set_entrance_exit_and_check`, `is_spanning_tree`.
- Used by:
  `maze_game.py`, indirectly by `game_app.py` via `maze_game`.
- Depends on:
  `grid_utils`, stdlib.
- Future fit:
  `domain/maze_generation.py`.
- Notes:
  fairly clean algorithm module.

### `grid_utils.py`

- Role:
  minimal grid primitives.
- Main classes:
  none.
- Main functions:
  `in_bounds`; constant `DIRS4`.
- Used by:
  `maze_game.py`, `maze_gen.py`, `enemies.py`.
- Depends on:
  stdlib only.
- Future fit:
  `domain/grid_utils.py`.
- Notes:
  clean utility module.

### `gameplay/formatting.py`

- Role:
  pure gameplay-related time formatting.
- Main classes:
  none.
- Main functions:
  `format_time`.
- Used by:
  `maze_game.py`, `gameplay/hud_text.py`, `state_machine/leaderboard_state.py`, tests.
- Future fit:
  keep in `gameplay/` or move later to `domain/formatting.py`.
- Notes:
  good example of low-risk extraction.

### `gameplay/maze_positions.py`

- Role:
  pure border-to-inner-cell translation helper for maze entry and exit setup.
- Main classes:
  none.
- Main functions:
  `inner_cell_from_border`.
- Used by:
  `maze_game.py`, tests.
- Depends on:
  stdlib only.
- Future fit:
  keep in `gameplay/` or move later to `domain/maze_positions.py`.
- Notes:
  extracted from nested `maze_game.py` scope as a Priority A pure helper.

### `gameplay/scoring.py`

- Role:
  pure score policy, score-input preparation, and score formula.
- Main classes:
  `ScoreParams`, `PreparedRunScore`.
- Main functions:
  `prepare_run_score`, `compute_score`.
- Used by:
  `maze_game.py`, tests.
- Future fit:
  keep in `gameplay/` or move later to `domain/scoring.py`.
- Notes:
  clean pure module; now also owns data-only preparation for runtime score calculation without taking over persistence or UI flow.

### `gameplay/result_text.py`

- Role:
  pure end-screen text builders and deterministic end-summary preparation.
- Main classes:
  `PreparedEndMenuSummary`.
- Main functions:
  `build_attempt_info`, `build_coin_types_line`, `build_highscore_line`, `build_end_menu_subtitle`, `prepare_end_menu_summary`.
- Used by:
  `maze_game.py`, tests.
- Depends on:
  `coins` for rarity icons, `gameplay.formatting` for best-time formatting.
- Future fit:
  `presentation/text/result_text.py` or keep in `gameplay/` until text helpers are grouped.
- Notes:
  pure helper module; now also owns deterministic preparation of best-time/highscore summary values before the pygame end-screen overlay is shown.

### `gameplay/hud_text.py`

- Role:
  pure HUD text assembly.
- Main classes:
  none.
- Main functions:
  `build_player_prefix`, `build_hud_text`.
- Used by:
  `maze_game.py`, tests.
- Depends on:
  `gameplay.formatting`.
- Future fit:
  `presentation/text/hud_text.py` or keep in `gameplay/` until presentation text helpers are grouped.
- Notes:
  pure helper module.

### `gameplay/__init__.py`

- Role:
  package marker.
- Used by:
  import system only.
- Future fit:
  keep as package marker.

### `state_machine/state_base.py`

- Role:
  FSM protocol and state manager.
- Main classes:
  `BaseState`, `StateManager`.
- Used by:
  `game_app.py`, all screen state modules.
- Depends on:
  `pygame`.
- Future fit:
  `state_machine/state_base.py` is already in the right package.
- Notes:
  clean, small coordination module.

### `state_machine/main_menu.py`

- Role:
  main menu screen with background/logo loading, animated appearance, keyboard/mouse handling.
- Main classes:
  `MainMenuState`.
- Main functions:
  state lifecycle methods and local render/asset helper methods.
- Used by:
  `game_app.py`.
- Depends on:
  `state_machine.state_base`, `ui`, `pygame`.
- Future fit:
  `state_machine/main_menu.py` is acceptable now; later asset-loading helpers could move to presentation helpers.
- Notes:
  very wide state module; combines screen logic, assets, layout, and animation.

### `state_machine/player_select_state.py`

- Role:
  player selection, player creation, player deletion confirmation, active-player change.
- Main classes:
  `PlayerSelectState`.
- Used by:
  `game_app.py`.
- Depends on:
  `state_machine.state_base`, `session_controller`, `players`, `ui`, `pygame`.
- Future fit:
  keep under `state_machine/`; later extract repeated modal/input helpers.
- Notes:
  mixes state logic, CRUD UI, keyboard input mode, and overlay rendering.

### `state_machine/mode_select_state.py`

- Role:
  round mode selection UI.
- Main classes:
  `ModeSelectState`.
- Used by:
  `game_app.py`.
- Depends on:
  `state_machine.state_base`, `session_controller`, `ui`, `pygame`.
- Future fit:
  keep under `state_machine/`.
- Notes:
  simpler state module; duplicated font and option rendering patterns remain.

### `state_machine/multiplayer_setup_state.py`

- Role:
  choose queue participants, create/delete players, apply rotate-queue configuration.
- Main classes:
  `MultiplayerSetupState`.
- Used by:
  `game_app.py`.
- Depends on:
  `state_machine.state_base`, `session_controller`, `players`, `ui`, `pygame`.
- Future fit:
  keep under `state_machine/`; later extract repeated player-management overlays.
- Notes:
  broad state module; overlaps behavior patterns with `player_select_state.py`.

### `state_machine/leaderboard_state.py`

- Role:
  leaderboard screen, scroll behavior, rendering of top runs and player aggregates.
- Main classes:
  `LeaderboardState`.
- Used by:
  `game_app.py`.
- Depends on:
  `state_machine.state_base`, `leaderboard`, `gameplay.formatting`, `session_controller`, `ui`, `pygame`.
- Future fit:
  keep under `state_machine/`; later extract table/scroll rendering helpers.
- Notes:
  wide read-only screen module with custom rendering and scrollbar logic.

### `state_machine/__init__.py`

- Role:
  package marker.

### `tests/test_formatting.py`

- Role:
  pure formatting assertions.
- Used by:
  pytest only.
- Future fit:
  keep under `tests/`.

### `tests/test_maze_positions.py`

- Role:
  pure assertions for border-to-inner-cell translation behavior.
- Used by:
  pytest only.
- Future fit:
  keep under `tests/`.

### `tests/test_scoring.py`

- Role:
  pure scoring assertions.
- Used by:
  pytest only.
- Future fit:
  keep under `tests/`.

### `tests/test_scoring_preparation.py`

- Role:
  pure assertions for score-input preparation before runtime score calculation.
- Used by:
  pytest only.
- Future fit:
  keep under `tests/`.

### `tests/test_result_text.py`

- Role:
  pure end-text formatting assertions.
- Used by:
  pytest only.
- Future fit:
  keep under `tests/`.

### `tests/test_hud_text.py`

- Role:
  pure HUD text assertions.
- Used by:
  pytest only.
- Future fit:
  keep under `tests/`.

### `tests/test_player_repository.py`

- Role:
  disposable-DB smoke tests for player repository behavior.
- Used by:
  pytest only.
- Depends on:
  `db_manager.init_db`, `db_manager.get_connection`, `persistence.player_repository`.
- Future fit:
  keep under `tests/`.
- Notes:
  uses `pytest` `tmp_path` and isolated temporary SQLite files; does not touch the working `maze_stats.db`.

### `tests/test_session_controller_record_run.py`

- Role:
  disposable-DB safety tests for the current `GameSessionController.record_run(...)` behavior.
- Used by:
  pytest only.
- Depends on:
  `db_manager.init_db`, `db_manager.get_connection`, `session_controller`.
- Future fit:
  keep under `tests/`.
- Notes:
  locks in the current `runs` insert, `player_stats` aggregate update, and `SessionStats` update contract on isolated temporary SQLite files; does not touch the working `maze_stats.db`.

### `tests/test_session_stats.py`

- Role:
  pure tests for runtime session aggregate behavior.
- Used by:
  pytest only.
- Depends on:
  `runtime.session_stats`.
- Future fit:
  keep under `tests/`.
- Notes:
  covers `add_result(...)` and `summary_line(...)` without pygame, SQLite, or repository dependencies.

### `tests/test_run_persistence.py`

- Role:
  non-pygame tests for the end-of-run persistence handoff helper.
- Used by:
  pytest only.
- Depends on:
  `runtime.run_persistence`, `runtime.session_stats`, `highscores`, `session_controller.RunResult`.
- Future fit:
  keep under `tests/`.
- Notes:
  covers JSON highscore updates, standalone `SessionStats` updates, and controller-path `RunResult` handoff without touching the working `maze_stats.db`.

### `tests/__init__.py`

- Role:
  tests package marker.

## Stage 3 Domain/Rendering Boundary Analysis

Current mixed-support conclusions:

- `coins.py`
  - previous mixed module:
    domain spawn/data + pygame drawing
  - current state:
    draw helpers moved to `presentation.coin_rendering`
- `blocks.py`
  - previous mixed module:
    runtime spawn/respawn + pygame drawing
  - current state:
    draw helpers moved to `presentation.block_rendering`
- `effects.py`
  - presentation-only today
  - not an immediate Stage 3 split target
- `palette.py`
  - presentation-only today
  - not an immediate Stage 3 split target

Option assessment for Stage 3:

- Option A: keep mixed modules as-is
  - lowest immediate risk
  - lowest architectural value
- Option B: extract narrow presentation helpers for `draw_*`
  - best near-term value/risk ratio
  - does not force package-wide moves
- Option C: full domain/presentation split into new packages
  - architecturally cleaner long-term
  - too wide for the current test surface and runtime coupling

Recommended next code-pass:

- completed: Option B narrow draw-path extraction for `coins.py` and `blocks.py`;
- next sensible Stage 3 target:
  do not combine further work with `maze_game.py` world-render extraction or `ui.py` cleanup in the same pass.

## HUD Rendering Boundary Analysis

Current HUD flow in `maze_game.py`:

- font setup:
  - `get_text_font(...)`
  - `get_emoji_font(...)`
- runtime values:
  - current player label
  - coin counters
  - `elapsed_ms_live`
- pure text assembly:
  - `gameplay.hud_text.build_hud_text(...)`
- mixed text rendering:
  - `ui.render_mixed_text(...)`
- background/surface composition:
  - padding calculation
  - HUD width/height calculation
  - `pygame.Surface(..., pygame.SRCALPHA)`
  - alpha fill `(0, 0, 0, 135)`
  - rounded background draw
- positioning/blit:
  - background at `(6, 4)`
  - text at `(6 + pad_x, 4 + pad_y)`

Ownership assessment:

- already extracted:
  - pure HUD text assembly
  - mixed text rendering
- still inline:
  - font setup
  - background/surface composition
  - positioning/blit

Best narrow future split:

- extract only the HUD surface/background composition helper first;
- keep gameplay values, font objects, and final blit positioning in `maze_game.py`.

## Dependency map

### Main runtime spine

- `game_app.py` -> `state_machine/*`
- `game_app.py` -> `session_controller.py`
- `game_app.py` -> `db_manager.py`
- `game_app.py` -> `highscore_adapter.py`
- `game_app.py` -> `maze_game.py`
- `maze_game.py` -> `gameplay/*`
- `maze_game.py` -> `maze_gen.py`
- `maze_game.py` -> `enemies.py`
- `maze_game.py` -> `coins.py`
- `maze_game.py` -> `blocks.py`
- `maze_game.py` -> `presentation.coin_rendering.py`
- `maze_game.py` -> `presentation.block_rendering.py`
- `maze_game.py` -> `effects.py`
- `maze_game.py` -> `presentation.enemy_sprites.py`
- `maze_game.py` -> `ui.py`
- `maze_game.py` -> `sounds.py`
- `maze_game.py` -> `sprites.py`
- `maze_game.py` -> `palette.py`
- `maze_game.py` -> `session_controller.py`
- `maze_game.py` -> `highscores.py`
- `maze_game.py` -> `runtime/run_persistence.py`

### Persistence spine

- `session_controller.py` -> `domain.player_models`
- `session_controller.py` -> `db_manager.py`
- `session_controller.py` -> `persistence.player_repository.py`
- `session_controller.py` -> `persistence.run_repository.py`
- `session_controller.py` -> `runtime/session_stats.py`
- `persistence/player_repository.py` -> `db_manager.py`
- `persistence/player_repository.py` -> `domain.player_models`
- `persistence/run_repository.py` -> `db_manager.py`
- `leaderboard.py` -> `db_manager.py`
- `highscore_adapter.py` -> `db_manager.py`
- `highscore_adapter.py` -> `highscores.py`
- `highscore_adapter.py` -> `persistence.player_repository.py`
- `maze_game.py` -> `highscores.py`
- `maze_game.py` -> `runtime/session_stats.py`
- `maze_game.py` -> `runtime/run_persistence.py`
- `maze_game.py` -> `session_controller.RunResult`

### Runtime spine

- `game_app.py` -> `maze_game.py`
- `game_app.py` -> `session_controller.py`
- `maze_game.py` -> `runtime/session_stats.py`
- `maze_game.py` -> `runtime/run_persistence.py`
- `session_controller.py` -> `runtime/session_stats.py`

### UI / screen spine

- `state_machine/main_menu.py` -> `ui.py`
- `state_machine/player_select_state.py` -> `domain.player_models`, `session_controller.py`, `ui.py`
- `state_machine/mode_select_state.py` -> `session_controller.py`, `ui.py`
- `state_machine/multiplayer_setup_state.py` -> `domain.player_models`, `session_controller.py`, `ui.py`
- `state_machine/leaderboard_state.py` -> `leaderboard.py`, `gameplay.formatting`, `ui.py`

## Structural findings

### God modules

- `maze_game.py` is the main god module by both line count and responsibility count.
- `game_app.py` is smaller, but still broad for an entrypoint because it owns bootstrap, menu assembly, and gameplay progression policy.
- `enemies.py` is large, but its responsibility is comparatively coherent.

### Mixed-responsibility modules

- `coins.py`: spawn/domain + rarity text helper; pygame rendering now lives in `presentation.coin_rendering.py`.
- `blocks.py`: spawn/respawn support; pygame rendering now lives in `presentation.block_rendering.py`.
- `ui.py`: text/font helpers + overlay rendering + blocking choice loops.

### State modules with repeated patterns

- `player_select_state.py` and `multiplayer_setup_state.py` duplicate player list, name input, delete confirm, and font setup patterns.
- `mode_select_state.py`, `leaderboard_state.py`, and `main_menu.py` repeat font setup and common render idioms.

### Coupling hotspots

- `maze_game.py` is the hub for almost every runtime-facing module.
- `ui.py` is shared across gameplay runtime and FSM screens.
- `session_controller.py` is shared across runtime and multiple screens.

## Runtime Boundary Analysis

### Runtime concerns found in current code

- app lifecycle and pygame process control
  - `game_app.run_game_app()`
  - `game_app.quit_game()`
- gameplay session orchestration
  - `game_app.GameplayWrapper`
  - `maze_game.play_maze(...)`
- active player / round mode / player rotation state
  - `session_controller.GameSessionController`
  - `session_controller.RoundMode`
- per-process session aggregates
  - `runtime.session_stats.SessionStats`
- current-run mutable state
  - local variables and closures inside `maze_game.play_maze()` / `run_once()`
- run result handoff between gameplay and persistence
  - `session_controller.RunResult`
- end-of-run persistence handoff branching
  - `runtime.run_persistence.handle_run_persistence`

### Runtime-related files

- `game_app.py`
  - responsibility:
    pygame bootstrap, main app loop, FSM wiring, gameplay launch, round-to-round control policy
  - dependencies:
    `pygame`, `state_machine/*`, `maze_game`, `session_controller`, `db_manager`, `highscore_adapter`
  - coupling:
    high
- `maze_game.py`
  - responsibility:
    current run execution, mutable run state, pause/end flow, runtime save branching
  - dependencies:
    very broad: gameplay helpers, presentation helpers, persistence-facing types, pygame
  - coupling:
    very high
- `session_controller.py`
  - responsibility:
    active-player state, session rotation, session-level caches, run-result recording
  - dependencies:
    `domain.player_models`, `persistence.player_repository`, `db_manager`, `runtime.session_stats`
  - coupling:
    high
- `runtime/session_stats.py`
  - responsibility:
    isolated runtime-only per-session aggregate state
  - dependencies:
    stdlib only
  - coupling:
    low
- `runtime/run_persistence.py`
  - responsibility:
    end-of-run persistence handoff branching between JSON, standalone session state, and controller-backed recording
  - dependencies:
    `highscores`, `session_controller.RunResult`
  - coupling:
    medium
- `state_machine/*`
  - responsibility:
    menu and setup screen runtime flow under the outer app loop
  - dependencies:
    `pygame`, `ui`, `session_controller`, selected domain/query modules
  - coupling:
    medium to high depending on state

### Candidate future runtime layer

Files and classes that could logically belong to a future runtime-oriented layer:

- `game_app.py`
  - `GameplayWrapper`
  - app lifecycle helpers
- `maze_game.py`
  - `play_maze(...)`
  - later split runtime flow/render/update helpers
- `session_controller.py`
  - `GameSessionController`
  - `RoundMode`
  - `RunResult` if it remains an application/runtime handoff type
- `runtime.session_stats.SessionStats`

Files that should not belong to runtime:

- `domain/player_models.py`
- `gameplay/*` pure helpers
- `persistence/player_repository.py`
- `leaderboard.py`
- `highscores.py`
- `db_manager.py`

### Recommendation on introducing `runtime/`

- current answer:
  later
- reasoning:
  - the runtime boundary is conceptually visible already;
  - but code ownership is not yet narrow enough to justify immediate physical moves;
  - introducing `runtime/` right now would likely mix package creation with broader import churn across `game_app.py`, `maze_game.py`, and `session_controller.py`;
  - the safer order is to finish one more narrow boundary step first, then introduce the package with delegation-style moves.

### Possible staged introduction

- Step A
  - define and document the runtime slice explicitly around:
    `GameSessionController`, `SessionStats`, round mode, gameplay wrapper
  - risk:
    low
- Step B
  - move `SessionStats` to a runtime/application-oriented module first, with minimal import churn
  - risk:
    medium
- Step C
  - move runtime orchestration modules behind a `runtime/` package boundary only after imports are already narrowed
  - risk:
    medium to high

## Run Recording Boundary Analysis

### Current run-recording flow

1. `maze_game.play_maze(...)`
   - detects end of run (`won` or `lost`)
   - computes `elapsed_ms`
   - computes final `score`
   - keeps per-run counters:
     - `coins_collected`
     - `bronze_count`
     - `silver_count`
     - `gold_count`
     - `diamond_count`
2. `maze_game.play_maze(...)`
   - if there is no `session_controller`, updates standalone `SessionStats` only
3. `maze_game.play_maze(...)`
   - if `session_controller` exists, constructs `RunResult` with:
     - `player_id`
     - `score`
     - `elapsed_ms`
     - `coins_value_sum`
     - `won`
     - per-rarity counts
4. `maze_game.play_maze(...)`
   - calls `session_controller.record_run(run_result)`
5. `GameSessionController.record_run(...)`
   - updates in-memory `SessionStats`
   - delegates one completed-run write to `persistence.run_repository`

### `record_run(...)` code breakdown after extraction

- runtime/application orchestration:
  - fetch per-player `SessionStats`
  - decide to update in-memory session aggregate before DB write
- runtime state update:
  - `stats.add_result(...)`
- repository delegation:
  - `write_completed_run(...)`
  - one completed-run DB transaction lives behind the persistence boundary

### Natural extraction boundary

Completed:

- keep `GameSessionController` as orchestration owner
- move SQL insert/update details into a dedicated persistence-facing write module

### Options

- Option A: keep `record_run(...)` inside `GameSessionController`
  - pluses:
    lowest immediate change risk
    no new boundary to test
  - minuses:
    keeps SQL details mixed with session orchestration
    makes future runtime/persistence separation harder
  - risk:
    low now, medium later
  - affected files:
    none for analysis; `session_controller.py` for any future code change
  - tests needed later:
    controller-level disposable-DB tests for `record_run(...)`

- Option B: extract SQL write path into `persistence/run_repository.py`
  - pluses:
    narrowest useful split
    keeps `GameSessionController` as runtime/application owner
    aligns with existing `persistence/player_repository.py`
    isolates the two SQL statements and aggregate-update policy close to persistence
  - minuses:
    requires defining a small write API carefully
    aggregate-update policy still needs a clear home inside the repository boundary
  - risk:
    medium
  - affected files:
    `session_controller.py`, new future `persistence/run_repository.py`, docs, new tests
  - tests needed later:
    disposable-DB tests for run insert and `player_stats` aggregate updates

- Option C: extract whole run recording into a separate service/recorder
  - pluses:
    can fully hide both session update and DB write behind one API
  - minuses:
    too broad for current project shape
    risks inventing a service layer before persistence boundary is settled
    likely duplicates responsibilities already present in `GameSessionController`
  - risk:
    medium to high
  - affected files:
    `session_controller.py`, `maze_game.py`, new service module, likely docs and more tests
  - tests needed later:
    repository tests plus service-level orchestration tests

### Recommended direction

- completed: Option B

Reason:

- it solves the tightest mixed concern in the smallest useful step;
- it preserves current ownership of runtime/session state in `GameSessionController`;
- it matches the extraction pattern already used for `player_repository`;
- it does not require moving `RunResult`, `RoundMode`, or the controller itself.

### Possible future code-pass

- Step 2A
  - completed: add disposable-DB tests for current `record_run(...)` behavior before moving SQL
  - risk:
    low
- Step 2B
  - completed: extract raw SQL write path into `persistence/run_repository.py`
  - completed: keep `GameSessionController.record_run(...)` as orchestration wrapper
  - risk:
    medium
- Step 2C
  - completed as part of Step 2B:
    1. update `SessionStats`
    2. call repository write API
  - risk:
    medium

## Gameplay Persistence Boundary Analysis

### Current end-of-run persistence flow

1. `maze_game.play_maze(...)`
   - computes final runtime values:
     - `elapsed_ms`
     - `score`
     - `coins_collected`
     - per-rarity counters
2. `maze_game.play_maze(...)`
   - updates legacy JSON highscore in memory and on disk:
     - `update_highscore_if_better(...)`
     - `save_highscore(...)`
3. `maze_game.play_maze(...)`
   - if there is no controller:
     - updates standalone `SessionStats`
4. `maze_game.play_maze(...)`
   - delegates persistence branching to `runtime.run_persistence.handle_run_persistence(...)`
   - inside that helper:
     - standalone mode updates `SessionStats`
     - controller mode constructs `RunResult`
     - controller mode calls `session_controller.record_run(...)`
5. `session_controller.record_run(...)`
   - updates runtime `SessionStats`
   - delegates SQLite write path to `persistence.run_repository.write_completed_run(...)`
6. `maze_game.play_maze(...)`
   - prepares end-screen summary values and shows blocking UI

### Responsibility zones

- score/value preparation
  - should stay in gameplay runtime
  - transfer risk:
    low
- JSON highscore path
  - does not naturally belong in core gameplay flow
  - transfer risk:
    medium
- standalone runtime aggregate update
  - partly justified in gameplay because controller-free mode exists
  - transfer risk:
    medium
- persistence orchestration handoff
  - can move out of `maze_game.py`
  - transfer risk:
    medium
- end-screen UI
  - should stay in `maze_game.py` for now
  - transfer risk:
    high

### Option assessment

- Option A: keep everything in `maze_game.py`
  - pluses:
    lowest immediate change risk
  - minuses:
    gameplay runtime still owns two persistence paths and save branching
  - risk:
    low now, medium later

- Option B: extract a narrow persistence handoff helper
  - pluses:
    best size-to-value ratio
    separates save-path branching from score prep and UI
  - minuses:
    helper signature will still be fairly explicit and wide
  - risk:
    medium

- Option C: extract a broader end-of-run coordinator
  - pluses:
    could hide more of the current end-of-run block
  - minuses:
    too broad for the current runtime/UI coupling
  - risk:
    medium to high

### Recommended direction

- completed: Option B via `runtime/run_persistence.py`;
- keep score preparation and blocking end-screen UI in `maze_game.py`;
- remaining Stage 4 question is ownership and lifecycle policy of `highscore.json`, not the basic branch mechanics.

## Legacy Highscore Ownership Analysis

### Current `highscore.json` flow

1. `highscore_adapter.py`
   - reads `highscore.json` through `highscores.load_highscore(...)` during startup migration
2. `runtime.run_persistence.handle_run_persistence(...)`
   - updates in-memory `Highscore`
   - writes `highscore.json` through `save_highscore(...)` on improvement
3. after migration
   - SQLite remains the main structured store
   - JSON still continues to receive runtime updates

### Current status

By actual code, `highscore.json` is:

- not the authoritative store for players/runs/leaderboard data
- not merely an archive
- an active compatibility output
- a transitional persistence artifact
- a startup migration source until the migration flag is present

### Compatibility contract

- one global legacy snapshot file
- updated only when a run improves that snapshot
- no per-player history guarantee
- no leaderboard or player-list guarantee
- not a full mirror of SQLite
- not the future primary persistence API

### Policy options

- Option A: keep JSON permanently as a second persistence path
  - risk:
    low now, medium later
- Option B: keep JSON as compatibility export only
  - risk:
    medium
- Option C: remove runtime JSON writes and make SQLite the sole active store
  - risk:
    medium to high

### Recommended direction

- prefer Option B
- do not remove runtime JSON writes before the compatibility contract is made explicit

### Cycles

No direct Python import cycle was found in the current module graph.

This is positive, but absence of cycles does not mean low coupling. The current design still has several high-centrality modules.

## Future placement map

Target grouping direction for later phases:

- `runtime/`
  - app entry and gameplay flow orchestration
- `state_machine/`
  - screen states and FSM primitives
- `domain/`
  - pure gameplay rules, generation, scoring, enemy logic, data models
- `presentation/`
  - pygame rendering, fonts, sprites, overlays, audio, visual effects
- `persistence/`
  - SQLite access, leaderboard queries, player repository, legacy adapters

The important constraint is sequence:

1. first extract pure logic and documentation boundaries;
2. then introduce thin internal boundaries;
3. only after that consider moving files physically.
