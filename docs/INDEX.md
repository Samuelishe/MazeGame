# Documentation Index

Read in this order for minimal token usage:

1. [PROJECT_STATE.md](PROJECT_STATE.md)  
   Current snapshot, entrypoints, main flows, important constraints.
2. [ARCHITECTURE.md](ARCHITECTURE.md)  
   Real module responsibilities, dependencies, runtime and persistence flow.
3. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)  
   Current layout, folder responsibilities, and near-term grouping plan.
4. [TECH_DEBT.md](TECH_DEBT.md)  
   Main architectural risks and stabilization targets.
5. [MODULES.md](MODULES.md)  
   File-level module map, ownership, dependency notes, and future placement hints.
6. [REFACTORING_PLAN.md](REFACTORING_PLAN.md)  
   Staged restructuring plan with risk and scope guidance.
7. [ROADMAP.md](ROADMAP.md)  
   Safe, incremental refactor plan.
8. [SESSION_LOG.md](SESSION_LOG.md)  
   Dated agent work history.

Supporting file:

- [../AGENTS.md](../AGENTS.md): agent-specific onboarding and operating rules.

## Quick facts

- Entrypoint: `game_app.py`
- Runtime interpreter: `.\.venv\Scripts\python.exe`
- Main gameplay loop: `maze_game.play_maze()`
- Pure gameplay helpers: `gameplay/`
- Player domain models: `domain/player_models.py`
- Player repository boundary: `persistence/player_repository.py`
- Run repository boundary: `persistence/run_repository.py`
- Runtime session aggregate: `runtime/session_stats.py`
- Gameplay persistence handoff helper: `runtime/run_persistence.py`
- Presentation helpers: `presentation/coin_rendering.py`, `presentation/block_rendering.py`
- Maze position helper: `gameplay/maze_positions.py`
- Score preparation helper: `gameplay/scoring.py`
- HUD text helpers: `gameplay/hud_text.py`
- Result summary text helpers: `gameplay/result_text.py`
- End-summary value preparation: `gameplay/result_text.py`
- Shared mixed text renderer: `ui.py::render_mixed_text`
- Repository smoke tests: `tests/test_player_repository.py`
- `record_run(...)` safety tests: `tests/test_session_controller_record_run.py`
- SessionStats tests: `tests/test_session_stats.py`
- Gameplay persistence handoff tests: `tests/test_run_persistence.py`
- Current Stage 3 mixed support hotspots: `coins.py`, `blocks.py`
- Module map: `docs/MODULES.md`
- Staged restructure plan: `docs/REFACTORING_PLAN.md`
- State screens: `state_machine/`
- Tests: `tests/`
- Main persistent store: `maze_stats.db` via SQLite
- Legacy persistent store still updated at runtime: `highscore.json`
- Runtime dependency: `pygame-ce`
- Test runner: `pytest`
