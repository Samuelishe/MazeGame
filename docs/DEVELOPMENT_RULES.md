# Development Rules

## Core principles

- Prefer boring architecture over clever architecture.
- Keep gameplay behavior stable unless the task explicitly allows behavior changes.
- Use small safe steps instead of large-scale rewrites.
- Prefer extract-before-rewrite.
- Use incremental refactoring only.
- Prefer composition over deep inheritance.
- Keep architecture concise.
- Avoid overengineering.

## Agent-driven development rules

- Read existing documentation before changing architecture-related code.
- Search before create: check whether similar logic already exists before adding helpers, classes, or abstractions.
- Do not introduce abstractions without at least two real use cases.
- Do not create utility dumping modules.
- Keep changes local, low-risk, and easy to review.
- Update docs whenever architecture, flow, or project rules change.
- Preserve current UX, controls, and return contracts unless explicitly approved otherwise.
- All user-facing responses must be written in Russian.
- Commit messages in final task summaries must remain in English.
- Final agent responses must include:
  1. changed files list
  2. brief description of changes
  3. behavior changes: yes/no
  4. checks and tests
  5. risks
  6. commit message

## Refactoring guardrails

- No behavior-changing refactors.
- No gameplay rewrites during stabilization passes.
- Use extract-first strategy for tangled code.
- Use small safe steps.
- Prefer package boundaries before file moves.
- Prefer documentation before restructuring.
- Avoid god modules when adding new code; do not make existing concentration worse.
- Avoid circular dependencies.
- Prefer explicit typing and useful docstrings.
- Do not add broad `except` blocks.
- Do not duplicate helpers, functions, or classes.
- Avoid mass file moves without a documented plan.
- Avoid large rewrites.
- Do not change gameplay behavior without explicit user approval.

## Documentation discipline

- Before any serious refactoring, read:
  - existing project documentation;
  - relevant module docstrings;
  - `docs/MODULES.md`;
  - `docs/ARCHITECTURE.md`;
  - `docs/REFACTORING_PLAN.md`.
- Update `docs/PROJECT_STATE.md` when runtime behavior or control flow changes.
- Update `docs/ARCHITECTURE.md` when module responsibilities or flow boundaries change.
- Update `docs/SESSION_LOG.md` after each meaningful architecture/stabilization pass.
- Keep docs aligned with real code, not intended future design.
- If architecture decisions change, update documentation in the same task.
- Every production module must be reflected in documentation.
- Keep `docs/MODULES.md`, `docs/ARCHITECTURE.md`, and `docs/INDEX.md` current.
- If a new production module is added, document it in the same task.

## Dependency and environment policy

- Avoid bleeding-edge dependency assumptions when a stable compatible option exists.
- Environment changes must be documented in project docs.
- Compatibility decisions must be recorded explicitly.
- Treat runtime environment as part of the architecture, not as incidental setup.
- Prefer stable drop-in replacements over custom patches when resolving compatibility problems.
- New dependencies are allowed when they reduce complexity, improve readability, improve testability, improve maintainability, improve UX, or improve reliability.
- Do not add dependencies "on spec" or without clear benefit.
- Do not add heavy dependencies without explicit project value.
- Do not duplicate capabilities already present in the codebase.
- When adding a dependency:
  - update `requirements.txt`;
  - update `README.md` if setup or usage changes;
  - explain the reason in the final report.

## Architecture inspection before file moves

Before moving files between packages:

- inspect imports;
- inspect dependency impact;
- evaluate test impact;
- update `docs/MODULES.md`;
- update `docs/REFACTORING_PLAN.md`.

## Required final response format

Every final agent response should include:

1. changed files list
2. brief description of changes
3. behavior changes: yes/no
4. checks and tests
5. risks / what to verify
6. commit message in English, 1-2 sentences
