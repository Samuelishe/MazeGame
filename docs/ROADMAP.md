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
- Stage 3 has now started with mixed domain/rendering boundary analysis.

## Next recommended implementation step

Stage 3 Step 1 code-pass:

1. extract only the pygame draw path from `coins.py`
2. extract only the pygame draw path from `blocks.py`
3. keep spawn/data/runtime logic in place
4. do not combine that pass with `maze_game.py` renderer extraction or `ui.py` cleanup

Why this next:

- it reduces mixed responsibilities in smaller modules first;
- it is safer than a broad `maze_game.py` rendering move;
- it builds a cleaner presentation boundary without changing gameplay rules.

## Near-term roadmap

### Phase A: Stage 3 mixed support cleanup

1. Narrow draw-helper extraction from `coins.py`
2. Narrow draw-helper extraction from `blocks.py`
3. Re-evaluate whether `ui.py` has a similarly small presentation-only split

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
