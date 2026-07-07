# File Organizer Refactoring

## What This Is

A technical debt cleanup and refactoring effort for the file organizer project. The goal is to remove unused legacy code by tracing imports from the main entry point, and to break down bloated functions and files into smaller, more focused modules to improve maintainability.

## Core Value

Keep the codebase lean and maintainable without altering the existing correct functionality.

## Requirements

### Validated

- ✓ The application successfully cleans, groups, routes, and organizes PDF documents.
- ✓ The core pipeline components (`organize.py`, `cleaning.py`, `grouping.py`, `routing.py`, etc.) work as expected.
- ✓ Identify and remove all unreachable legacy code that is not imported or used by the main application flow. (Validated in Phase 01: legacy-code-cleanup)

### Active

- [ ] Refactor bloated files into separate focused modules.
- [ ] Refactor oversized functions into smaller, single-purpose functions.

### Out of Scope

- Adding new features or altering existing behavior (pure refactoring).
- Changing the underlying runtime or infrastructure.

## Context

- There is significant legacy code not used by the main application flow (often referred to via `organizer.py` / `organize.py`).
- We are taking an aggressive refactoring approach by breaking code into separate modules rather than just splitting functions within the same files.
- The project has a codebase map outlining the existing architecture and pipeline.
- Phase 01 successfully removed all unused code by tracing imports.

## Constraints

- **Functional Parity**: The refactoring must not break existing functionality or change the output format.
- **Maintainability**: The new modules should have clear, single responsibilities.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Break bloated code into new modules | Improves maintainability and file sizes over keeping them in the same file. | — Pending |
| Trace imports from entry point | Safest way to identify truly unused legacy code without false positives. | — Completed (Phase 01) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-07 after Phase 01 completion*
