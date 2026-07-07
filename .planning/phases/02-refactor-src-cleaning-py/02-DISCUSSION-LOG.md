# Phase 02: Refactor src/cleaning.py - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-07
**Phase:** 02-Refactor src/cleaning.py
**Areas discussed:** Module Breakdown, Date Parsing Logic, API Interface

---

## Module Breakdown

| Option | Description | Selected |
|--------|-------------|----------|
| Create a new src/cleaning/ package | Create a new src/cleaning/ package with files like dates.py, tenants.py, and models.py | ✓ |
| Flatten the logic | Flatten the logic into src/processing/ alongside grouping.py and routing.py | |

**User's choice:** Create a new src/cleaning/ package with files like dates.py, tenants.py, and models.py
**Notes:** Decided to encapsulate the cleaning domain within its own sub-package.

---

## Date Parsing Logic

| Option | Description | Selected |
|--------|-------------|----------|
| Keep it in src/cleaning/dates.py | Keep it encapsulated within the cleaning package as it's primarily used during cleaning | ✓ |
| Extract to src/core/date_utils.py | Extract it to a globally available shared utility | |

**User's choice:** Keep it in src/cleaning/dates.py as it's primarily used during the cleaning phase
**Notes:** The massive 200-line heuristic date parser will remain domain-specific.

---

## API Interface

| Option | Description | Selected |
|--------|-------------|----------|
| Create an \_\_init\_\_.py facade | Create an \_\_init\_\_.py in src/cleaning/ that exports a process_cleaning_phase facade function | ✓ |
| Direct imports | Have organize.py directly import from orchestrator.py or submodules | |

**User's choice:** Create an \_\_init\_\_.py in src/cleaning/ that exports a process_cleaning_phase facade function, hiding the internal modules
**Notes:** Facade pattern keeps integration boundaries stable for `src/organize.py`.

---

## the agent's Discretion

None

## Deferred Ideas

None
