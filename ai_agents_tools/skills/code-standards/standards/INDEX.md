# Code Structure & Writing Guidelines — Index

Top-level reference for the `code-structure-*` rules. Each rule is a separate `.mdc` file that loads in context only when its trigger condition fires (see Trigger column).

## Mental Model

- Plans commit to **layer + logical unit + responsibility**. They do *not* commit to file paths.
- Code is organized by **layer** (top-level) and **logical unit** (folder-per-concept, recursive).
- Each logical unit owns everything it needs: types, exceptions, logger, decorators.
- Cross-layer dependencies always flow through `Protocol`s, never concrete classes.
- Configuration lives in one place (`config/`) but mirrors the source tree internally.

## Top-Level Layer Set

The standard layers, used by all rules. Don't invent new top-level layers casually.

```
project/
├── core/          # Domain models + pure business logic. No I/O, no frameworks.
├── services/      # Orchestration. Coordinates core + adapters.
├── adapters/      # External integrations: API clients, DBs, queues, file I/O.
├── api/           # HTTP entry point.
├── cli/           # CLI entry point.
├── config/        # Centralized settings, constants, env loading.
└── tests/         # Mirrors source tree at the layer level.
```

### Dependency direction (one-way only)

```
api ──┐
cli ──┼──▶ services ──▶ adapters ──▶ (external world)
      │                     │
      └────────────────────▶┴──▶ core
```

`config/` is reachable from anywhere but imports from nowhere else in the project.

## The Rules

| Rule | Trigger | Purpose |
|---|---|---|
| `code-structure-layout.mdc` | **Always-on** | Layers, folder-per-unit, `__init__.py` public API |
| `code-structure-typing.mdc` | **Always-on** | Type hints non-negotiable; `mypy --strict` passes |
| `code-structure-encapsulation.mdc` | Errors / loggers / decorators | Each unit owns its exceptions, logger, decorators |
| `code-structure-config.mdc` | Touching `config/`, env vars, constants | Central config, mirrors source tree |
| `code-structure-protocols.mdc` | Cross-layer interfaces, `ports/` folders | One `Protocol` per file; consumer-side definition |
| `code-structure-tests.mdc` | Touching `tests/` | Tests mirror layers, flatten within layers |
| `code-structure-development-workflow.mdc` | Bug fixes, E2E testing, general coding | Reproduce bugs realistically; obsess over UI precision; proactively fix lint and test issues |
| `code-structure-solid.mdc` | Designing classes/services | SOLID with Python-specific examples |
| `code-structure-composition.mdc` | Designing class structure | Composition over inheritance; classes over loose functions |
| `code-structure-file-length.mdc` | Files approaching 400 lines, or new files | 400 line target, 450 hard ceiling |
| `code-structure-entry-points.mdc` | Touching `cli/` or `api/` | Entry points are thin wrappers over services |
| `code-structure-planning.mdc` | Writing a plan document | Plans use `Structure:` blocks, not `Files:` blocks |

## How to Use

- **code-standards skill:** rules are bundled in `standards/` next to the skill's `SKILL.md`. Load via `standards/INDEX.md`, then read applicable files from `standards/`.
- **Cursor:** drop these into `.cursor/rules/`. Globs and `alwaysApply` flags handle attachment automatically.
- **Other agents:** reference the relevant rule by name in your prompt, e.g. "follow `code-structure-encapsulation` when handling errors."
- **Plans:** the `code-structure-planning` rule replaces the `**Files:**` block in `writing-plans` tasks with a `**Structure:**` block.
