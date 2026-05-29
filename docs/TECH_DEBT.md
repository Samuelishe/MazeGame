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

Why partially safe:

- logic is local and reusable
- but it depends on pygame fonts and surfaces

Dependencies/coupling:

- `pygame.font.Font`
- `pygame.Surface`

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

- highscore summary value preparation is still local to `maze_game.py`
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

Why safe:

- deterministic text formatting only
- can be tested independently

Dependencies/coupling:

- highscore values
- preformatted time strings

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

- inner-cell coordinate translation
- score/result value preparation
- highscore summary value preparation

Completed low-coupling extractions now include:

- inner-cell coordinate translation
- score/result value preparation

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
  inner-cell helper, HUD mixed-text renderer, score/result value preparation, highscore summary value preparation
- Priority B:
  enemy sprite loading, spawn/setup cluster, coin collection handler, world render helper, update-step helpers
- Priority C:
  pause handling, event handling, end-screen blocking control flow, whole-`run_once()` extraction
