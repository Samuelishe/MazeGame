# Roadmap

## Goal

Keep gameplay stable while continuing small, testable architectural improvements.

## Current status

- Stage 2 `maze_game.py` Priority A extractions are completed.
- Stage 4 persistence boundary work is largely completed:
  - `domain/player_models.py`
  - `persistence/player_repository.py`
  - `persistence/run_repository.py`
  - `runtime/session_stats.py`
  - `runtime/run_persistence.py`
  - `players.py` removed
  - `highscore.json` compatibility contract documented
- Stage 3 Step 1 analysis is completed.
- Stage 3 Step 2 narrow draw-path extraction is completed:
  - `presentation/coin_rendering.py`
  - `presentation/block_rendering.py`

## Next recommended implementation step

Next Stage 3 follow-up:

1. keep `coins.py` and `blocks.py` stable after the narrow draw split
2. reassess `maze_game.py` world-render extraction separately
3. do not combine that future pass with `ui.py` cleanup

Why this next:

- the first presentation boundary already exists now;
- the next useful move is broader and therefore should stay separate;
- this keeps Stage 3 incremental instead of turning into a package rewrite.

## Near-term roadmap

### Phase A: Stage 3 mixed support cleanup

1. Completed: narrow draw-helper extraction from `coins.py`
2. Completed: narrow draw-helper extraction from `blocks.py`
3. Re-evaluate whether `maze_game.py` world rendering or `ui.py` has a similarly safe next split

### Phase B: Stage 5 state-screen duplication cleanup

1. Compare `player_select_state.py` and `multiplayer_setup_state.py`
2. Extract only shared input/list boilerplate if behavior can stay identical
3. Keep screen flow and UX unchanged

### Phase C: Stage 3 deeper presentation work

1. Reassess `maze_game.py` world-render helper extraction
2. Reassess HUD surface/background extraction
3. Keep pause/end-screen flow out of scope unless there is a narrower boundary

### Phase D: Stage 4 policy follow-up

1. Keep `highscore.json` behavior unchanged for now
2. Only later decide whether legacy JSON stays as explicit compatibility export or is retired

## Work that should remain deferred

- broad runtime package moves
- full `maze_game.py` decomposition in one pass
- `highscore.json` behavior changes
- schema changes without a migration plan
- package-wide presentation moves
- broad UI rewrites
