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

## Low-risk cleanup

### 11. Small copy/paste drift in state modules

Some state classes still show repeated declarations and minor local duplication.

Why it matters:

- low immediate risk
- worth cleaning only in narrowly scoped passes

### 12. Documentation lag risk

Because the project is moving in small steps, docs can drift from code quickly if not updated every pass.

Why it matters:

- onboarding quality depends on docs staying synchronized with reality

### 13. Limited test coverage

The project now has initial tests, but they still cover only a small pure-logic slice:

- time formatting
- HUD text
- scoring
- result summary text

Not yet covered:

- session progression
- DB write paths
- migration behavior
- runtime/FSM integration

Why it matters:

- regression safety is improving, but still limited

## Safe extraction candidates

These are realistic next targets for extract-only refactors.

### 1. HUD text assembly helpers

Risk level: low

Why safe:

- mostly deterministic string assembly
- does not require changing event flow or timing

Dependencies/coupling:

- current counters and preformatted time values from `maze_game.py`

### 2. HUD mixed-text rendering helper

Risk level: low to medium

Why partially safe:

- logic is local and reusable
- but it depends on pygame fonts and surfaces

Dependencies/coupling:

- `pygame.font.Font`
- `pygame.Surface`

### 3. End-screen result summary text

Risk level: low

Current status:

- already extracted into `gameplay/result_text.py`

Why it was safe:

- pure string assembly
- no event-flow or render-flow changes

### 4. Highscore summary formatting

Risk level: low

Why safe:

- deterministic text formatting only
- can be tested independently

Dependencies/coupling:

- highscore values
- preformatted time strings

### 5. Lightweight result value container

Risk level: medium

Why not yet low-risk:

- introduces a new state shape
- touches more runtime code than pure text extraction

Dependencies/coupling:

- scoring
- highscore update path
- session stats/persistence hooks

### 6. Pause/end-menu control-flow extraction

Risk level: medium to high

Why dangerous now:

- tightly coupled to nested runtime loops
- easy to change timing or input semantics accidentally

Dependencies/coupling:

- pygame event flow
- timer adjustment logic
- current run-return contract

## Analysis notes for `maze_game.py`

### Pure helper groups

Already identified and/or extracted:

- time formatting
- HUD text assembly
- scoring
- end-screen result text assembly

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

### Runtime-only logic

Current runtime-only slices inside `maze_game.py`:

- movement stepping
- enemy advancement
- block respawn/timer updates
- collision detection
- pause timer offset handling

### Low-coupling candidates

The lowest-coupling candidates remain runtime-independent text/formatting helpers and similar deterministic value formatting. These are safe because they do not alter input flow, timing, mutable run state, or persistence behavior.
