# Technical Debt

This document reflects the current project state after the completed stabilization passes:

- `.venv` + Python 3.14 environment alignment
- `pygame-ce` compatibility fix
- loop-based gameplay progression
- first `gameplay/` package extraction
- first focused unit tests

The project is more stable than before, but the main structural hotspots are still real and should be addressed incrementally.

## High-risk debt

### 1. `maze_game.py` remains a god module

`maze_game.py` still combines:

- gameplay rules
- runtime state mutation
- input handling
- rendering
- HUD/end-screen preparation
- some pygame-dependent HUD rendering helpers
- persistence hooks
- resource setup

Why it matters:

- changes have a large blast radius
- the module is hard to reason about locally
- it remains the single highest-risk edit surface in the project

Detailed inspection confirms that the real problem is not only file size, but also dense internal clustering inside `play_maze()`:

- session bootstrap
- asset loading
- entity spawning
- event/pause flow
- simulation updates
- rendering
- score and persistence hooks
- end-screen blocking UI flow

Most of these concerns still live inside one nested `run_once()` function.

### 2. Mixed runtime/render/gameplay responsibilities

The main gameplay loop still owns multiple concerns at once:

- simulation advancement
- collision/timer updates
- visual drawing
- user-facing summary preparation
- UI overlay flow

Why it matters:

- extraction requires more care than it should
- testability is weaker than a cleaner separation would allow

### 3. Nested runtime loops

The app still relies on:

- the top-level app/FSM pygame loop
- nested gameplay loop logic in `maze_game.py`
- blocking pause/end-screen interaction flow

Why it matters:

- control flow is harder to reason about
- timing-sensitive changes remain risky

### 4. Direct pygame coupling

Core runtime code still depends directly on pygame objects and services:

- surfaces
- events
- display lifecycle
- fonts
- ticks/timers

Why it matters:

- only pure helper slices can be extracted safely
- renderer separation does not yet exist

The detailed `maze_game.py` inspection shows three different pygame-coupling levels:

- low:
  score/value preparation and text/value summary composition
- medium:
  HUD surface preparation, asset loading, world rendering helpers
- high:
  event flow, pause menu timing offsets, end-screen blocking choice flow

## Medium-risk debt

### 5. No centralized runtime state object

Active run state is still distributed across local mutable variables and closures inside `play_maze()`.

Examples:

- player/goal positions
- timing data
- enemy/block collections
- score counters
- win/loss flags

Why it matters:

- state is harder to inspect and evolve
- function structure and runtime behavior are tightly coupled

### 6. Lack of renderer separation

Rendering code still lives inside the main gameplay runtime flow instead of behind even a small dedicated boundary.

Why it matters:

- gameplay and presentation concerns are still entangled
- extraction beyond pure text helpers remains medium risk

### 6A. Mixed support modules still need broader presentation cleanup

The first narrow Stage 3 cleanup is now completed:

- `coins.py`
  - coin data, rarity configuration, spawn logic, and rarity text helper remain in place
  - pygame coin drawing moved out
- `blocks.py`
  - block spawn/respawn logic remains in place
  - pygame block drawing moved out

Why it matters:

- this confirms that narrow presentation boundaries can be introduced safely;
- broader renderer cleanup still remains for `maze_game.py` and `ui.py`;
- the project now has a real `presentation/` package without broad restructuring.

Current Stage 3 conclusion:

- completed:
  extract draw-path helpers only;
- `effects.py` and `palette.py` still do not show the same mixed-responsibility problem.

### 7. Partial package migration

The codebase has started moving pure logic into `gameplay/`, but most runtime/support files remain root-level.

Why it matters:

- documented structure and physical structure are only partially aligned
- further grouping must stay incremental

### 8. Remaining root-level flat structure

Most production modules still sit in the repository root.

Why it matters:

- ownership boundaries are still weak
- future package grouping will require continued discipline

### 9. Duplicated UI boilerplate in state classes

Several `state_machine/` screens still repeat:

- font initialization
- mouse navigation handling
- overlay/input-mode patterns

Why it matters:

- UI cleanup remains repetitive
- there is still no thin shared presentation layer for repeated state-class behavior

### 10. Split persistence ownership

The project still writes to both:

- `maze_stats.db`
- `highscore.json`

Why it matters:

- save behavior still has two active paths
- future persistence simplification needs explicit migration handling

### 11. Persistence boundaries are still blurred

The persistence layer is present, but ownership inside it is still uneven:

- `db_manager.py` is infrastructure-only and clean;
- `leaderboard.py` is a coherent read-only query module;
- `session_controller.py` still owns session/application orchestration, but raw SQL write logic has been moved out;
- `highscores.py` keeps a second active persistence path alive during normal gameplay;
- `highscore_adapter.py` is clean as a migration bridge, but it encodes transitional policy.

Why it matters:

- the gameplay runtime still knows about two save systems;
- application flow and repository logic are too tightly coupled;
- future Stage 4 refactors need to separate responsibilities without changing save behavior.

### 12. `SessionStats` ownership was corrected

`SessionStats` now lives in `runtime/session_stats.py`, which matches its actual role better.

What the code shows:

- it is mutable in-memory state for the current process only;
- it is created and managed by `GameSessionController`;
- it is also instantiated directly by `maze_game.py` when gameplay runs without a controller;
- it is never stored as its own persistence record.

Why it matters:

- the main ownership problem is solved;
- the runtime-state ownership is now explicit in the import graph.

### 13. Runtime boundary exists partially, but broader migration is not in place

Current runtime concerns are spread across:

- `game_app.py`
- `maze_game.py`
- `session_controller.py`
- `runtime/session_stats.py`
- `state_machine/*`

Why it matters:

- ownership is understandable only after reading several files together;
- broader `runtime/` adoption would still risk combining multiple medium-coupling moves into one step.

## Low-risk cleanup

### 14. Small copy/paste drift in state modules

Some state classes still show repeated declarations and minor local duplication.

Why it matters:

- low immediate risk
- worth cleaning only in narrowly scoped passes

### 15. Documentation lag risk

Because the project is moving in small steps, docs can drift from code quickly if not updated every pass.

Why it matters:

- onboarding quality depends on docs staying synchronized with reality

### 16. Limited test coverage

The project now has initial tests, but they still cover only a small pure-logic slice:

- time formatting
- HUD text
- scoring
- result summary text

Not yet covered:

- session progression
- most DB write paths beyond player repository smoke coverage
- migration behavior
- runtime/FSM integration

Why it matters:

- regression safety is improving, but still limited
- Stage 4 now has minimal isolated safety nets for both `persistence.player_repository.py` and `GameSessionController.record_run(...)`, which lowers risk for further repository-boundary work but still does not cover migration paths.

## Persistence Architecture

### Current flow

- DB bootstrap:
  `game_app.init_environment()` -> `db_manager.init_db(...)`
- legacy migration:
  `game_app.init_environment()` -> `highscore_adapter.migrate_highscore_if_needed(...)`
- player/profile loading:
  `GameSessionController.from_db(...)` -> `persistence.player_repository.load_players(...)`
- default-player bootstrap:
  `GameSessionController.from_db(...)` / `GameSessionController.__post_init__()` -> `persistence.player_repository.get_or_create_player(...)`
- player writes:
  `GameSessionController.create_player(...)` / `delete_player_from_session(...)` -> `persistence.player_repository.create_player(...)` / `persistence.player_repository.delete_player(...)`
- run writes:
  `maze_game.play_maze()` -> `session_controller.record_run(...)`
- leaderboard reads:
  `state_machine/leaderboard_state.py` -> `leaderboard.get_top_scores(...)`, `leaderboard.get_players_sorted(...)`
- legacy runtime highscores:
  `maze_game.play_maze()` -> `highscores.load_highscore(...)`, `update_highscore_if_better(...)`, `save_highscore(...)`

### Main boundary problems

- runtime save behavior is split across SQLite and JSON in the same gameplay path;
- `persistence/player_repository.py` is now the dedicated player CRUD/profile-loading slice;
- `session_controller.py` combines:
  - round mode and active-player policy;
  - session lifecycle and player list management;
  - run-recording orchestration;
- `persistence/run_repository.py` now owns raw SQL writes for completed runs and aggregate updates;
- the gameplay runtime still constructs `RunResult` directly and knows when SQLite writes happen;
- migration code is isolated, but the migrated legacy path still remains active afterward.

## Persistence Refactoring Candidates

### 1. Compatibility cleanup after player boundary extraction

Risk level: medium

Why:

- the repository and runtime boundaries are now isolated, and the compatibility cleanup around the removed `players.py` file is complete.

Target outcome:

- completed: player models are separable from SQLite CRUD code;
- completed: `SessionStats` no longer shares a file with repository functions.

Compatibility cleanup status:

- completed: `PlayerAggregateStats` and `PlayerProfile` moved to `domain.player_models.py`;
- completed: repository CRUD functions moved to `persistence.player_repository.py`;
- completed: `SessionStats` moved to `runtime.session_stats.py`;
- completed: production imports no longer depend on `players.py`.

### `SessionStats` analysis

Current direct usage surface:

- `maze_game.py`
  - bootstrap lookup/creation
  - standalone write path through `add_result(...)`
  - end-summary read path through `summary_line()`
- `session_controller.py`
  - in-memory cache keyed by player id
  - bootstrap/create/delete/rotation maintenance
  - end-of-run updates via `record_run(...)`

Classification:

- runtime state:
  yes
- session aggregate:
  yes
- persistence model:
  no
- service object:
  no
- stable domain model:
  weak fit

Recommended direction:

- completed: move to `runtime/session_stats.py`;
- completed: production compatibility imports from `players.py` were removed and the file is no longer part of the active import graph.

### 2. Extract run-recording repository boundary

Risk level: medium

Why:

- `session_controller.record_run(...)` is the tightest coupling point between application flow and SQL writes.

Target outcome:

- completed: SQLite write details moved behind a narrower API;
- `GameSessionController` is now closer to orchestration and session policy.

### Run Recording Boundary Analysis

Current `record_run(...)` responsibilities are:

- update runtime `SessionStats`
- delegate into `persistence.run_repository`

Why this matters:

- it is the tightest remaining join point between runtime/application logic and raw SQL writes;
- it is also the next place where Stage 4 can gain a real architectural boundary without touching gameplay flow.

Best current extraction target:

- completed: a narrow persistence write module for run insertion and aggregate updates.

Recommended next direction:

- completed: add dedicated disposable-DB tests for `record_run(...)` behavior;
- completed: extract SQL details into `persistence/run_repository.py`;
- completed: keep `GameSessionController.record_run(...)` as the orchestration wrapper.

### 3. Narrow gameplay knowledge of persistence

Risk level: medium

Why:

- `maze_game.py` still knows about:
  - JSON highscore updates;
  - `RunResult` construction;
  - the split between controller-present and controller-absent save behavior.

Target outcome:

- gameplay runtime keeps result data preparation, but knows less about save-path details.

### Gameplay Persistence Boundary Analysis

Current code facts:

- `maze_game.py` no longer updates `highscore.json` inline;
- `maze_game.py` no longer decides inline whether to update standalone `SessionStats` or create `RunResult` and call `session_controller.record_run(...)`;
- that branching now lives in `runtime/run_persistence.py`.

Why this matters:

- the remaining coupling is no longer raw SQL;
- it is now mostly gameplay runtime knowledge of persistence policy through helper usage and highscore lifecycle assumptions;
- this keeps `maze_game.py` narrower, but does not yet solve legacy JSON ownership.

Recommended narrow next target:

- completed: a smaller persistence handoff helper now owns:
  - JSON highscore update;
  - standalone vs controller-present result recording decision;
  - `RunResult` creation and `record_run(...)` invocation.

What should stay in `maze_game.py` for now:

- end-of-run value preparation from live runtime state;
- end-screen UI and blocking choice flow.

### 4. Clarify legacy JSON ownership

Risk level: medium

Why:

- `highscore.json` is both a migrated legacy source and an active runtime sink.

Current interpretation from code:

- active compatibility output;
- transitional persistence artifact;
- not merely archival while gameplay still writes it after completed runs.

Compatibility contract to preserve for now:

- one global legacy snapshot file;
- update-on-improvement behavior only;
- no promise of per-player history or full SQLite parity;
- no claim that JSON is the primary persistence API.

Target outcome:

- explicit decision whether JSON remains compatibility output, archival output, or removable legacy path.

### Legacy Highscore Ownership Analysis

Current code shows:

- `highscore.json` is read by `highscore_adapter.py` during startup migration;
- `highscore.json` is written during gameplay through `runtime.run_persistence.py`;
- no runtime read path besides startup migration depends on JSON after gameplay begins;
- SQLite already owns players, runs, and leaderboard data.

What this means:

- JSON is not the authoritative application store;
- JSON is not purely archival either;
- JSON is best described as an active compatibility output and transitional persistence artifact.

Main risk if runtime writes are removed too early:

- the file becomes stale for any user or external workflow that still expects live updates;
- migration for future fresh DBs would only see the last exported JSON snapshot, not newer SQLite-only progress;
- the product would silently change its compatibility behavior.

Recommended direction:

- prefer compatibility-export semantics over permanent dual-write ownership;
- do not remove runtime writes until the compatibility contract is explicitly documented.

## Stage 3 focus after Stage 4

Stage 4 has reduced the persistence hotspot enough that the next best low-risk architecture work is no longer another repository split.

Current recommended Stage 3 target:

- completed:
  - `presentation/coin_rendering.py`
  - `presentation/block_rendering.py`

Next recommended Stage 3 target:

- do not widen the change surface immediately;
- keep world-render extraction as a separate future pass.

### Enemy asset-loading hotspot after the first presentation split

Current code facts:

- `maze_game.py` no longer hardcodes enemy sprite paths inline;
- `maze_game.py` no longer performs `SpriteSheet.from_file(...)` calls directly;
- fallback-to-red loading behavior now lives in `presentation/enemy_sprites.py`;
- `EnemyType -> SpriteSheet` mapping now lives in `presentation/enemy_sprites.py`;
- per-enemy `AnimatedSprite(...)` creation happens immediately afterward.

Why it matters:

- this is a smaller Stage 3 target than full world-render extraction;
- it is more presentation-oriented than enemy AI/spawn logic;
- it is still coupled enough to runtime that only the asset-loading half should move first.

Recommended next move:

- completed: extract enemy sprite loading and type mapping only;
- keep `AnimatedSprite(...)` creation and runtime randomization in `maze_game.py`.

### HUD rendering composition is still inline in `maze_game.py`

Current code facts:

- `gameplay.hud_text.build_hud_text(...)` is already extracted;
- `ui.render_mixed_text(...)` is already reused for the HUD surface;
- `maze_game.py` still owns:
  - HUD font object setup
  - HUD padding math
  - HUD background surface creation
  - alpha/background behavior
  - final positioning and blit

Why it matters:

- this is a narrower Stage 3 target than full world-render extraction;
- it is more presentation-oriented than gameplay state advancement;
- it can likely move without touching pause/end-screen behavior.

Recommended next move:

- completed: extract HUD surface/background composition only;
- keep runtime values, font setup, and final positioning in `maze_game.py`.

### Coin collection handler after the current Stage 3 presentation splits

Current code facts:

- `maze_game.py` still owns local `try_collect_at(position, current_ms)`;
- the helper linearly scans the active `coins` list;
- it mutates:
  - `coins_collected`
  - bronze/silver/gold/diamond counters
  - the `coins` list itself
- it also triggers:
  - `sound.play_coin()` or `sound.play_diamond()`
  - `effects.add_coin_flash(...)`
- the helper returns nothing and works through outer-scope mutation only.

Why it matters:

- this is a narrower runtime-support target than enemy update extraction;
- it is still smaller than world-render extraction;
- it mixes local gameplay accounting with presentation side effects in one inline helper.

Recommended next move:

- completed: narrow extraction of the coin collection helper only;
- `runtime/coin_collection.py` now owns lookup/removal, rarity/value accounting, and sound/effect triggers;
- movement branches, goal checks, enemy updates, and block timers remain in `maze_game.py`.

### Block timer update slice after the coin collection split

Current code facts:

- block timing still lives inline in `maze_game.py`;
- every block owns its own `expires_at`;
- `blocked_set` is rebuilt from active block positions;
- expiration recomputes forbidden cells from:
  - player
  - goal
  - enemies
  - other blocks
- respawn uses existing `respawn_block(...)` from `blocks.py`;
- timer reset is `block.expires_at = now_ms + block_lifetime_ms`.

Important clarification:

- there is no separate `next_block_respawn_at`;
- there is no separate `BLOCK_RESPAWN_MS`;
- the real timing model is per-block expiration plus shared lifetime.

Why it matters:

- this is now the cheapest remaining narrow runtime-support extraction target in `maze_game.py`;
- it is more local and more testable than enemy update extraction;
- it is still smaller than world-render extraction.

Recommended next move:

- completed: narrow `update_block_timers(...)` extraction only;
- `runtime/block_timers.py` now owns blocked-set rebuild, expiration checks, forbidden-cell recomputation, respawn calls, and `expires_at` resets;
- initial spawn, pause-time shifts, movement flow, enemy updates, and rendering remain in `maze_game.py`.

What should wait:

- full `maze_game.py` renderer extraction
- `ui.py` cleanup in the same pass
- broad `presentation/` package moves

## Safe extraction candidates

These are realistic next targets for extract-only refactors.

### 1. Entry/exit inner-cell helper

Risk level: low

Why safe:

- pure coordinate conversion
- no pygame dependency
- no persistence coupling

Dependencies/coupling:

- border coordinate and side string only

### 2. HUD text assembly helpers

Risk level: low

Why safe:

- mostly deterministic string assembly
- does not require changing event flow or timing

Dependencies/coupling:

- current counters and preformatted time values from `maze_game.py`

### 3. HUD mixed-text rendering helper

Risk level: low to medium

Why it was partially safe:

- logic is local and reusable
- but it depends on pygame fonts and surfaces

Dependencies/coupling:

- `pygame.font.Font`
- `pygame.Surface`

Current status:

- completed by reusing `ui.render_mixed_text(...)`
- HUD positioning and background drawing remain in `maze_game.py`

### 4. Score/result value preparation

Risk level: low to medium

Why relatively safe:

- the score formula is already externalized
- remaining work is mostly assembling explicit input values
- can be separated from UI wait logic

Dependencies/coupling:

- elapsed time
- coin counters
- `ScoreParams`
- local `won/lost` flags

Current status:

- partially extracted into `gameplay/scoring.py` via pure score-input preparation

Remaining work:

- highscore summary value preparation is now extracted into `gameplay/result_text.py`
- score preparation is now separated, but persistence and end-screen UI flow are still in the same runtime block

### 5. End-screen result summary text

Risk level: low

Current status:

- already extracted into `gameplay/result_text.py`

Why it was safe:

- pure string assembly
- no event-flow or render-flow changes

### 6. Highscore summary formatting

Risk level: low

Why it was safe:

- deterministic text formatting only
- can be tested independently

Dependencies/coupling:

- highscore values
- preformatted time strings

Current status:

- extracted into `gameplay/result_text.py` as deterministic end-summary preparation
- pygame overlay flow and persistence hooks remain in `maze_game.py`

### 7. Enemy sprite loading and type mapping

Risk level: medium

Why not low-risk:

- uses pygame image loading and asset paths
- fallback behavior must remain identical

Dependencies/coupling:

- `pygame`
- `SpriteSheet`
- `EnemyType`
- resource file paths

### 8. Runtime spawn/setup cluster

Risk level: medium

Why not low-risk:

- combines safe-zone computation, enemy spawn, animation setup, block spawn, coin spawn, timers, and counters
- strongly tied to local mutable run state

Dependencies/coupling:

- `enemies`
- `blocks`
- `coins`
- `sprites`
- timer values and player/goal positions

### 9. Coin collection handler

Risk level: medium

Why not low-risk:

- mutates multiple counters and the `coins` collection
- triggers sound and visual effects

Dependencies/coupling:

- `CoinRarity`
- `SoundBank`
- `Effects`
- current coin list and counters

### 10. Lightweight result value container

Risk level: medium

Why not yet low-risk:

- introduces a new state shape
- touches more runtime code than pure text extraction

Dependencies/coupling:

- scoring
- highscore update path
- session stats/persistence hooks

### 11. World render helper

Risk level: medium

Why not low-risk:

- presentation-only in spirit
- but depends on a large live state surface: maze, blocks, coins, enemies, trail, effects, palette, cell size

Dependencies/coupling:

- `pygame`
- almost all visual runtime collections

### 12. Pause/end-menu control-flow extraction

Risk level: medium to high

Why dangerous now:

- tightly coupled to nested runtime loops
- easy to change timing or input semantics accidentally

Dependencies/coupling:

- pygame event flow
- timer adjustment logic
- current run-return contract

## Analysis notes for `maze_game.py`

### Internal zone map

Approximate line map:

- `1-66`: header + imports
- `68-75`: type alias + constants
- `78-154`: top-level helpers
- `156-216`: `play_maze()` entry setup
- `218-903`: nested `run_once()`
- `907-933`: outer replay/new-level loop

Within `run_once()`:

- `228-240`: border-to-inner cell helper
- `243-311`: enemy sprite asset loading
- `314-396`: HUD font setup + mixed-text HUD renderer
- `398-500`: enemy/block/coin spawn and initial state setup
- `501-524`: coin collection handler
- `526-592`: input and pause flow
- `594-605`: auto-movement
- `607-652`: enemy processing
- `654-669`: block timer processing
- `671-677`: collision detection
- `679-746`: world rendering
- `748-784`: HUD rendering
- `786-897`: score, persistence, and end-screen flow

### Pure helper groups

Already identified and/or extracted:

- time formatting
- HUD text assembly
- scoring
- end-screen result text assembly

Remaining low-coupling helper candidates:

- none in Priority A scope

Completed low-coupling extractions now include:

- inner-cell coordinate translation
- score/result value preparation
- highscore summary value preparation
- HUD mixed-text rendering helper

These remain the safest pattern for continued incremental cleanup.

### State containers

There is still no dedicated centralized runtime state container. The closest thing is a set of local variables grouped by concern inside `play_maze()`.

### Rendering clusters

Current visible clusters inside `play_maze()`:

- maze/background cell rendering
- actor/object rendering
- HUD rendering
- end-screen overlay rendering

### UI-only logic

Current UI-only slices inside `maze_game.py`:

- pause-menu interaction
- end-screen summary preparation
- HUD line rendering helper
- HUD surface/background composition
- enemy sprite asset loading

### Runtime-only logic

Current runtime-only slices inside `maze_game.py`:

- movement stepping
- enemy advancement
- block respawn/timer updates
- collision detection
- pause timer offset handling
- entity spawn/setup for enemies, blocks, and coins

### Low-coupling candidates

The lowest-coupling candidates remain runtime-independent text/formatting helpers and similar deterministic value formatting. These are safe because they do not alter input flow, timing, mutable run state, or persistence behavior.

Priority ranking after detailed inspection:

- Priority A:
  completed
- Priority B:
  enemy sprite loading, spawn/setup cluster, coin collection handler, world render helper, update-step helpers
- Priority C:
  pause handling, event handling, end-screen blocking control flow, whole-`run_once()` extraction
