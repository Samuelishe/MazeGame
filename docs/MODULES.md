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

### State machine / screen flow

- `state_machine/state_base.py`
- `state_machine/main_menu.py`
- `state_machine/player_select_state.py`
- `state_machine/mode_select_state.py`
- `state_machine/multiplayer_setup_state.py`
- `state_machine/leaderboard_state.py`

### Gameplay domain and gameplay support

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

- `ui.py`
- `sounds.py`
- `sprites.py`

### Persistence / session / leaderboard data

- `db_manager.py`
- `players.py`
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

## Module catalogue

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
  `coins`, `effects`, `gameplay/*`, `highscores`, `sounds`, `sprites`, `players`, `grid_utils`, `enemies`, `blocks`, `palette`, `ui`, `maze_gen`, `session_controller`.
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
    `gameplay.formatting`, `gameplay.scoring`, `gameplay.result_text`, `highscores`, `session_controller`, `players.SessionStats`, `ui`, `pygame`.
  - extraction risk:
    high as one block; medium if split into value preparation vs UI wait.

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
  `db_manager`, `players`.
- Future fit:
  `persistence/session_controller.py` or `application/session_controller.py`.
- Notes:
  not a gameplay module, but still broad because it combines session coordination and direct SQL write orchestration; this is the main Stage 4 boundary hotspot.

### `db_manager.py`

- Role:
  SQLite connection setup, PRAGMA management, schema bootstrap, meta flags.
- Main classes:
  none.
- Main functions:
  `get_connection`, `init_db`, `set_meta_flag`, `get_meta_flag`.
- Used by:
  `game_app.py`, `session_controller.py`, `players.py`, `leaderboard.py`, `highscore_adapter.py`.
- Depends on:
  stdlib only.
- Future fit:
  `infrastructure/db_manager.py`.
- Notes:
  clean infrastructure module; root placement is the main issue, not internal design.

### `players.py`

- Role:
  player profiles, aggregate stats model, CRUD for players, in-memory `SessionStats`.
- Main classes:
  `PlayerAggregateStats`, `PlayerProfile`, `SessionStats`.
- Main functions:
  `load_players`, `create_player`, `delete_player`, `get_player_by_name`, `get_or_create_player`.
- Used by:
  `maze_game.py`, `session_controller.py`, `highscore_adapter.py`, `state_machine/player_select_state.py`, `state_machine/multiplayer_setup_state.py`.
- Depends on:
  `db_manager`.
- Future fit:
  split between `domain/player_models.py` and `persistence/player_repository.py`.
- Notes:
  one file holds both domain dataclasses and DB access, and also owns in-memory `SessionStats`; this is a clear mixed-responsibility module and the second major Stage 4 hotspot.

#### `players.py` decomposition analysis

- Approximate internal groups:
  - domain/player read models:
    `PlayerAggregateStats`, `PlayerProfile`
  - repository helper:
    `_row_to_aggregate_stats(...)`
  - repository API:
    `load_players(...)`, `create_player(...)`, `delete_player(...)`, `get_player_by_name(...)`, `get_or_create_player(...)`
  - runtime/session state:
    `SessionStats`

- Entity classification:
  - `PlayerAggregateStats`
    - type:
      domain model representing persisted aggregate player stats
    - used by:
      `PlayerProfile`, `players.py` repository functions, state-machine player list rendering indirectly
    - dependencies:
      stdlib dataclass/types only
  - `PlayerProfile`
    - type:
      domain model for active player identity plus optional aggregate stats
    - used by:
      `session_controller.py`, `state_machine/player_select_state.py`, `state_machine/multiplayer_setup_state.py`
    - dependencies:
      `PlayerAggregateStats`
  - `_row_to_aggregate_stats(...)`
    - type:
      repository mapping utility
    - used by:
      `load_players(...)`, `get_player_by_name(...)`
    - dependencies:
      `sqlite3.Row`, `PlayerAggregateStats`
  - `load_players(...)`
    - type:
      repository read API
    - used by:
      `GameSessionController.from_db(...)`
    - dependencies:
      `db_manager.get_connection`, `_row_to_aggregate_stats`, `PlayerProfile`
  - `create_player(...)`
    - type:
      repository write API
    - used by:
      `GameSessionController.create_player(...)`
    - dependencies:
      `db_manager.get_connection`, `PlayerProfile`, `PlayerAggregateStats`
  - `delete_player(...)`
    - type:
      repository delete API
    - used by:
      `GameSessionController.delete_player_from_session(...)`
    - dependencies:
      `db_manager.get_connection`
  - `get_player_by_name(...)`
    - type:
      repository read API
    - used by:
      `get_or_create_player(...)`
    - dependencies:
      `db_manager.get_connection`, `_row_to_aggregate_stats`, `PlayerProfile`
  - `get_or_create_player(...)`
    - type:
      repository convenience API
    - used by:
      `GameSessionController.from_db(...)`, `GameSessionController.__post_init__()`, `highscore_adapter.py`
    - dependencies:
      `get_player_by_name(...)`, `create_player(...)`
  - `SessionStats`
    - type:
      runtime session state, not a persistence model
    - used by:
      `maze_game.py`, `session_controller.py`
    - dependencies:
      stdlib only

- Highest-risk dependencies:
  - `GameSessionController` depends on both repository functions and `SessionStats` from the same module.
  - `maze_game.py` imports `SessionStats` directly for no-controller runtime mode.
  - `highscore_adapter.py` depends on `get_or_create_player(...)`, which keeps migration logic tied to the mixed module.

- Safe future split candidates:
  - `PlayerAggregateStats` and `PlayerProfile` into a pure models module
  - `_row_to_aggregate_stats(...)` plus CRUD functions into a repository-oriented module

- Cautious future split candidates:
  - `SessionStats`, because it is imported directly by both `maze_game.py` and `session_controller.py`
  - `get_or_create_player(...)`, because it is used in controller bootstrap and migration bootstrap paths

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
   - reads players via `players.load_players(...)`
   - may create a default player via `players.get_or_create_player(...)`
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

- `players.py`
  - domain logic:
    `PlayerAggregateStats`, `PlayerProfile`, parts of `SessionStats`.
  - persistence logic:
    `load_players`, `create_player`, `delete_player`, `get_player_by_name`, `get_or_create_player`, row mapping.
  - mixed incorrectly:
    yes; domain models, repository code, and session-only memory state are combined.

- `session_controller.py`
  - domain logic:
    `RoundMode`, `RunResult`, current-player rotation policy.
  - persistence logic:
    `record_run(...)` SQL insert/update path, defensive DB init in lifecycle methods.
  - mixed incorrectly:
    yes; application/session orchestration and repository-style writes are combined.

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

- `players.py` split candidate
  - target:
    separate player data models from player repository functions and session-only stats.
  - risk:
    medium.

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
  tiny module; current root placement is unnecessary.

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
  rendering-only concern.

### `blocks.py`

- Role:
  temporary blocking wall model, spawn/respawn behavior, and rendering.
- Main classes:
  `Block`.
- Main functions:
  `spawn_blocks`, `respawn_block`, `draw_block_cell`.
- Used by:
  `maze_game.py`.
- Depends on:
  `pygame`, stdlib.
- Future fit:
  split between `domain/blocks.py` and `presentation/block_rendering.py`, or keep together under `gameplay/blocks.py` until a renderer boundary exists.
- Notes:
  mixes gameplay placement logic with pygame drawing.

### `coins.py`

- Role:
  coin rarity definitions, spawn logic, coin rendering.
- Main classes:
  `CoinRarity`, `RarityConfig`, `Coin`.
- Main functions:
  `spawn_coins`, `rarity_icon`, `draw_coin`.
- Used by:
  `maze_game.py`, `gameplay/result_text.py`.
- Depends on:
  `pygame`, stdlib.
- Future fit:
  split between `domain/coins.py` and `presentation/coin_rendering.py`, or keep together under `gameplay/coins.py` until rendering split is justified.
- Notes:
  another mixed domain/rendering module.

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

### `tests/__init__.py`

- Role:
  tests package marker.

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
- `maze_game.py` -> `effects.py`
- `maze_game.py` -> `ui.py`
- `maze_game.py` -> `sounds.py`
- `maze_game.py` -> `sprites.py`
- `maze_game.py` -> `palette.py`
- `maze_game.py` -> `session_controller.py`
- `maze_game.py` -> `highscores.py`

### Persistence spine

- `session_controller.py` -> `db_manager.py`
- `session_controller.py` -> `players.py`
- `players.py` -> `db_manager.py`
- `leaderboard.py` -> `db_manager.py`
- `highscore_adapter.py` -> `db_manager.py`
- `highscore_adapter.py` -> `highscores.py`
- `highscore_adapter.py` -> `players.py`

### UI / screen spine

- `state_machine/main_menu.py` -> `ui.py`
- `state_machine/player_select_state.py` -> `session_controller.py`, `players.py`, `ui.py`
- `state_machine/mode_select_state.py` -> `session_controller.py`, `ui.py`
- `state_machine/multiplayer_setup_state.py` -> `session_controller.py`, `players.py`, `ui.py`
- `state_machine/leaderboard_state.py` -> `leaderboard.py`, `gameplay.formatting`, `ui.py`

## Structural findings

### God modules

- `maze_game.py` is the main god module by both line count and responsibility count.
- `game_app.py` is smaller, but still broad for an entrypoint because it owns bootstrap, menu assembly, and gameplay progression policy.
- `enemies.py` is large, but its responsibility is comparatively coherent.

### Mixed-responsibility modules

- `coins.py`: spawn/domain + rendering.
- `blocks.py`: spawn/domain + rendering.
- `players.py`: domain models + repository operations + session aggregate object.
- `ui.py`: text/font helpers + overlay rendering + blocking choice loops.

### State modules with repeated patterns

- `player_select_state.py` and `multiplayer_setup_state.py` duplicate player list, name input, delete confirm, and font setup patterns.
- `mode_select_state.py`, `leaderboard_state.py`, and `main_menu.py` repeat font setup and common render idioms.

### Coupling hotspots

- `maze_game.py` is the hub for almost every runtime-facing module.
- `ui.py` is shared across gameplay runtime and FSM screens.
- `session_controller.py` is shared across runtime and multiple screens.

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
