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

## Refactoring guardrails

- No behavior-changing refactors.
- No gameplay rewrites during stabilization passes.
- Use extract-first strategy for tangled code.
- Avoid god modules when adding new code; do not make existing concentration worse.
- Avoid circular dependencies.
- Prefer explicit typing and useful docstrings.
- Do not add broad `except` blocks.
- Do not duplicate helpers, functions, or classes.

## Documentation discipline

- Update `docs/PROJECT_STATE.md` when runtime behavior or control flow changes.
- Update `docs/ARCHITECTURE.md` when module responsibilities or flow boundaries change.
- Update `docs/SESSION_LOG.md` after each meaningful architecture/stabilization pass.
- Keep docs aligned with real code, not intended future design.

## Dependency and environment policy

- Avoid bleeding-edge dependency assumptions when a stable compatible option exists.
- Environment changes must be documented in project docs.
- Compatibility decisions must be recorded explicitly.
- Treat runtime environment as part of the architecture, not as incidental setup.
- Prefer stable drop-in replacements over custom patches when resolving compatibility problems.

## Required final response format

Every final agent response should include:

1. changed files list
2. brief description of changes
3. behavior changes: yes/no
4. risks / what to verify
5. commit message in English, 1-2 sentences
