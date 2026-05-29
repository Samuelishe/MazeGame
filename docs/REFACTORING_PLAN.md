# Refactoring Plan

## Purpose

This plan describes the recommended future restructuring path after the architecture inspection pass.

It is intentionally conservative:

- no large-scale rewrite;
- no package-wide move in one step;
- no gameplay behavior changes;
- no UX changes unless explicitly requested.

## Stage 1

- Goal:
  strengthen architecture visibility and freeze safe boundaries before code movement.
- Expected result:
  complete module map, agreed target structure, updated architecture docs, clearer ownership language.
- Risk:
  low.
- Estimated change size:
  docs only.

## Stage 2

- Goal:
  continue extract-first work inside `maze_game.py` without changing gameplay behavior.
- Expected result:
  more pure helpers move out of `maze_game.py` into existing or narrowly scoped modules.
- Candidate targets:
  gameplay result value preparation, non-pygame calculations, enemy/coin/block decision helpers, text/value formatting that still lives in runtime flow.
- Risk:
  low to medium.
- Estimated change size:
  small code changes across 2-5 files plus focused tests.

Concrete `maze_game.py` steps inside Stage 2:

1. extract inner-cell border translation helper from `run_once()`
2. extract score/result value preparation from the end-of-run block
3. extract highscore summary value preparation from the end-of-run block
4. extract HUD mixed-text rendering helper out of nested local scope

These are the current Priority A candidates from the detailed `maze_game.py` inspection.

Current Stage 2 progress:

- completed: inner-cell border translation helper
- completed: score/result value preparation
- completed: highscore summary value preparation
- completed: HUD mixed-text rendering helper

Stage 2 status:

- Priority A extraction work is completed.

## Stage 3

- Goal:
  reduce mixed responsibilities in support modules.
- Expected result:
  clearer separation between domain logic and pygame rendering in modules such as `coins.py`, `blocks.py`, and parts of `ui.py`.
- Candidate targets:
  move rendering helpers behind presentation-oriented modules while leaving public behavior unchanged.
- Risk:
  medium.
- Estimated change size:
  medium, several small passes instead of one rewrite.

Concrete `maze_game.py`-adjacent steps inside Stage 3:

1. extract enemy sprite loading and sprite-type mapping into a presentation helper
2. extract world rendering block into a dedicated pygame render helper
3. extract HUD background/surface composition into a presentation helper
4. separate presentation pieces from mixed support modules such as `coins.py` and `blocks.py`

## Stage 4

- Goal:
  stabilize the persistence layer boundaries.
- Expected result:
  clearer distinction between:
  player/session domain models,
  repository/query code,
  migration code,
  runtime save orchestration.
- Candidate targets:
  keep `session_controller.py` focused on session coordination, continue narrowing gameplay persistence knowledge, and clarify legacy JSON ownership.
- Risk:
  medium.
- Estimated change size:
  medium, 3-6 files plus tests for non-pygame behavior.

Persistence Architecture focus for Stage 4:

- separate player data models from repository functions;
- separate session orchestration from SQLite run-write implementation;
- narrow gameplay runtime knowledge of active save-path details;
- clarify the intended runtime role of `highscore.json` after migration.

Concrete `maze_game.py`-adjacent steps inside Stage 4:

1. isolate the value-preparation side of run persistence from the blocking end-screen UI flow
2. reduce direct knowledge of SQLite write-path details at the gameplay-runtime boundary

Concrete future Stage 4 steps:

1. Narrow `maze_game.py` persistence knowledge
   - goal:
     reduce gameplay awareness of `RunResult` construction and save-path branching without touching end-screen UI flow.
   - risk:
     medium.
   - expected result:
     gameplay runtime still prepares end-of-run values, while persistence orchestration becomes less embedded in the blocking end-of-run branch.
   - files:
     `maze_game.py`, `session_controller.py`

2. Clarify legacy JSON highscore policy
   - goal:
     define whether `highscore.json` stays as compatibility output, archive output, or removable legacy path.
   - risk:
     medium because behavior is user-visible.
   - expected result:
     explicit product/architecture decision before any removal or demotion work.
   - files:
     `highscores.py`, `highscore_adapter.py`, `maze_game.py`, docs only at first

3. Preserve read-only leaderboard boundary while documenting it as the stable query slice
  - goal:
    keep `leaderboard.py` coherent and separate it conceptually from write-side refactors.
  - risk:
    low.
  - expected result:
    Stage 4 changes do not accidentally destabilize leaderboard reads.
  - files:
    `leaderboard.py`, `docs/MODULES.md`, `docs/ARCHITECTURE.md`

Stage 4 Step 1 status:

- completed: `players.py` decomposition analysis
- completed: first safe model split into `domain/player_models.py`

`players.py` implementation-oriented follow-up after this analysis:

1. Step 1A: separate player data models on paper and then in code
   - goal:
     move `PlayerAggregateStats` and `PlayerProfile` behind a clean model boundary first.
   - risk:
     low to medium.
   - expected result:
     typed player objects stop depending on repository placement.
   - files:
     completed: `players.py`, `session_controller.py`, `state_machine/player_select_state.py`, `state_machine/multiplayer_setup_state.py`, `domain/player_models.py`

2. Step 1B: isolate repository helper and CRUD/read APIs
   - goal:
     keep `_row_to_aggregate_stats(...)` and player CRUD/profile-loading functions together as one repository slice.
   - risk:
     medium.
   - expected result:
     the player repository can move without bringing `SessionStats` with it.
   - files:
     completed: `players.py`, `session_controller.py`, `highscore_adapter.py`, `persistence/player_repository.py`

3. Step 1C: move `SessionStats` only after runtime call sites are narrowed
   - goal:
     avoid a premature split that forces broad touch points in gameplay and session orchestration at the same time.
   - risk:
     medium.
   - expected result:
     session-only memory state leaves `players.py` last, after repository and model boundaries are already stable.
   - files:
     completed: `players.py`, `maze_game.py`, `session_controller.py`, `runtime/session_stats.py`

Stage 4 Step 1 status:

- completed: Step 1A model split into `domain/player_models.py`
- completed: Step 1B repository split into `persistence/player_repository.py`
- completed: Step 1C SessionStats split into `runtime/session_stats.py`
- completed: minimal disposable-DB smoke tests for `persistence.player_repository.py`
- completed: disposable-DB safety tests for current `GameSessionController.record_run(...)`
- completed: Stage 4 Step 2B run-write extraction into `persistence/run_repository.py`
- completed: remove the now-unused `players.py` compatibility shim from the production import graph
- completed: extract a narrow gameplay persistence handoff helper around JSON highscore update and controller/standalone result recording
- next sensible candidate: clarify `highscore.json` ownership policy or find a smaller post-handoff persistence slice around gameplay result reporting

Gameplay Persistence Boundary recommendation after analysis:

- completed: the narrow persistence handoff helper now owns:
  - JSON highscore update;
  - standalone `SessionStats` recording;
  - `RunResult` creation;
  - `session_controller.record_run(...)` delegation;
- keep score preparation and blocking end-screen UI in `maze_game.py`;
- do not expand this into a broad end-of-run coordinator until there is a clearer low-risk slice.

SessionStats recommendation after analysis:

- do not move `SessionStats` into `domain/` by default;
- preferred long-term target is a runtime/application-oriented module because actual usage is process-lifetime mutable session state;
- completed: the narrow boundary step landed and `SessionStats` now lives in `runtime/session_stats.py`.

Runtime boundary recommendation after analysis:

- do not introduce `runtime/` by a broad file-move pass right now;
- completed: one narrow runtime-state move for `SessionStats`;
- only after that introduce `runtime/` as a visible package boundary for orchestration modules if import pressure is already reduced.

## Stage 5

- Goal:
  reduce duplication across state modules.
- Expected result:
  small shared helpers for font initialization, player-list overlays, simple confirmation/input patterns.
- Candidate targets:
  `player_select_state.py`, `multiplayer_setup_state.py`, `mode_select_state.py`, `leaderboard_state.py`.
- Risk:
  medium.
- Estimated change size:
  medium, but must be sliced into narrow passes because screen behavior is sensitive.

Concrete `maze_game.py` caution for Stage 5:

- do not combine state-screen cleanup with `maze_game.py` event-flow extraction in the same step
- pause/end-screen control-flow changes should remain separate because they are higher risk than normal screen cleanup

## Stage 6

- Goal:
  introduce directory boundaries before physical moves.
- Expected result:
  new documented internal ownership model:
  `runtime`, `domain`, `presentation`, `persistence`, `state_machine`.
- Candidate approach:
  new modules appear in target packages first while old root modules delegate gradually.
- Risk:
  medium to high if done too early.
- Estimated change size:
  medium across multiple safe steps.

## Stage 7

- Goal:
  perform physical file relocation only after imports and boundaries are already stable.
- Expected result:
  fewer root-level modules, clearer package layout, minimal behavior risk because logic boundaries were prepared earlier.
- Preconditions:
  existing tests expanded, docs already aligned, helper extractions already landed, import graph simplified.
- Risk:
  high if attempted prematurely; medium if delayed until prerequisites are met.
- Estimated change size:
  medium to large, but should still be split by slice.

## Stage 8

- Goal:
  decide final persistence ownership of legacy `highscore.json`.
- Expected result:
  either explicit archival-only status or complete runtime removal.
- Risk:
  medium because persistence behavior is user-visible.
- Estimated change size:
  small to medium, but needs explicit product decision first.

## Priority order

Recommended next implementation order:

1. Stage 4
2. Stage 5
3. Stage 3
4. Stage 6
5. Stage 7
6. Stage 8

Reason:

- `maze_game.py` remains the highest leverage extraction target.
- persistence boundaries are the next most important architectural clarity problem.
- state-machine duplication matters, but it is less urgent than reducing runtime concentration.
- physical file moves should be delayed until boundary work is already done.
- Stage 3 presentation extraction remains a valid alternative next step, but Stage 4 persistence-boundary analysis is the recommended default after Stage 2 completion.

## `maze_game.py` extraction priority

### Priority A

- completed

### Priority B

- enemy sprite loading and type mapping
- enemy/block/coin spawn setup cluster
- coin collection handler
- auto-movement / enemy update / block update helpers
- world render helper

### Priority C

- pause handling
- full event handling extraction
- end-screen blocking control flow
- whole `run_once()` extraction
