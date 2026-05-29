# Roadmap

## Goal

Stabilize the codebase for future agent-driven work without breaking gameplay.

## Phase 1: Safe stabilization

1. Replace recursive replay flow in `GameplayWrapper.start_level()` with an explicit loop.
2. Extract pure utility functions from `maze_game.py` only when they have no pygame side effects.
3. Move shared formatting helpers like time formatting out of `maze_game.py` into a neutral utility module.
4. Add narrow tests for:
   - `compute_score()`
   - `format_time()`
   - `GameSessionController.advance_after_run()`
   - `record_run()` DB effects
   - highscore migration behavior

## Phase 2: Runtime boundary cleanup

1. Introduce a small `RunState` dataclass for active round variables.
2. Separate end-of-run persistence from render/input logic.
3. Isolate resource loading paths for:
   - audio
   - enemy sprite sheets
   - fonts

## Phase 3: Gameplay decomposition

1. Split `maze_game.py` by responsibility, not by arbitrary size:
   - scoring
   - runtime model
   - gameplay loop
   - HUD/end screen integration
2. Keep public behavior unchanged while moving code.
3. Avoid package/module renames unless there is a concrete migration plan.

## Phase 4: Persistence simplification

1. Decide whether `highscore.json` should remain runtime-active or become read-only legacy data.
2. If SQLite becomes sole source of truth, deprecate JSON writes behind a deliberate migration step.
3. Document the final authoritative record source in `README.md` and `AGENTS.md`.

## Improvements with low gameplay risk

- Add tests for pure/data modules
- Centralize formatting helpers
- Remove duplicate UI boilerplate
- Add small asset-path helpers
- Clean up repeated attribute declarations
- Add structured logging notes to `SESSION_LOG.md`

## Changes that should wait for explicit approval

- turning gameplay into a full FSM state class
- changing save-file format ownership
- renaming modules
- changing package layout
- broad UI rewrites
