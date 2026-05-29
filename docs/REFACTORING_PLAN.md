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
- remaining: HUD mixed-text rendering helper

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
  split `players.py` responsibilities; keep `session_controller.py` focused on session coordination.
- Risk:
  medium.
- Estimated change size:
  medium, 3-6 files plus tests for non-pygame behavior.

Concrete `maze_game.py`-adjacent steps inside Stage 4:

1. isolate the value-preparation side of run persistence from the blocking end-screen UI flow
2. reduce direct knowledge of SQLite write-path details at the gameplay-runtime boundary

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

1. Stage 2
2. Stage 4
3. Stage 5
4. Stage 3
5. Stage 6
6. Stage 7
7. Stage 8

Reason:

- `maze_game.py` remains the highest leverage extraction target.
- persistence boundaries are the next most important architectural clarity problem.
- state-machine duplication matters, but it is less urgent than reducing runtime concentration.
- physical file moves should be delayed until boundary work is already done.

## `maze_game.py` extraction priority

### Priority A

- HUD mixed-text renderer

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
