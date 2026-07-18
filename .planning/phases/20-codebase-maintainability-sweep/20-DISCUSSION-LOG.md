# Phase 20: Codebase Maintainability Sweep - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-18T13:12:05+03:00
**Phase:** 20-codebase-maintainability-sweep
**Areas discussed:** Type checking validation, Typing style consistency, Private method docstrings, Test files scope, Architecture for FS-UI

---

## Type checking validation

| Option | Description | Selected |
|--------|-------------|----------|
| (Recommended) Just add hints for IDEs | keeps the codebase sweep focused and avoids configuration rabbit holes | ✓ |
| Set up mypy | standard static type checker | |
| Set up pyright | faster, tighter IDE integration | |
| You decide | | |

**User's choice:** Just add hints for IDEs
**Notes:** User asked why not use mypy/pyright. Explained scope and configuration rabbit hole risks. User agreed to just add hints for IDEs.

---

## Typing style consistency

| Option | Description | Selected |
|--------|-------------|----------|
| (Recommended) Yes, enforce modern built-in generics | aligns with CONVENTIONS.md and reduces `typing` imports | ✓ |
| No, stick to whatever is already there | | |
| You decide | | |

**User's choice:** (Recommended) Yes, enforce modern built-in generics (aligns with CONVENTIONS.md and reduces `typing` imports)
**Notes:** 

---

## Private method docstrings

| Option | Description | Selected |
|--------|-------------|----------|
| (Recommended) Only public interfaces | strictly meets requirements, saves time | |
| Public interfaces AND complex private methods | better long-term maintainability | ✓ |
| You decide | | |

**User's choice:** Public interfaces AND complex private methods (better long-term maintainability)
**Notes:** User explicitly instructed: "modify maint-01 to require docstrings for every single function". `REQUIREMENTS.md` was updated mid-discussion to reflect this.

---

## Architecture (Future FS-UI)

| Option | Description | Selected |
|--------|-------------|----------|
| N/A | Interactive custom question | ✓ |

**User's choice:** Keep core pipeline functional, use classes for future FS-UI orchestration.
**Notes:** User asked if the current implementation was okay or if we should use a class-based approach. Clarified that functional is best for the pipeline, but classes are best for the upcoming FS-UI listener. Updated `PROJECT.md`, `ROADMAP.md`, `REQUIREMENTS.md`, and `STATE.md` to lock in this hybrid architecture.

---

## Test files scope

| Option | Description | Selected |
|--------|-------------|----------|
| (Recommended) Strictly main source code (`src/`) | keeps the sweep focused and manageable | |
| Both `src/` and `tests/` | maximum maintainability | ✓ |
| You decide | | |

**User's choice:** Both `src/` and `tests/` — maximum maintainability
**Notes:**

---

## the agent's Discretion

None

## Deferred Ideas

- Use class-based orchestration for the new File-System UI watcher (Phase 24).
