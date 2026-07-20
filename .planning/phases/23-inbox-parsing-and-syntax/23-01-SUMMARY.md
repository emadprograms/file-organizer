---
phase: 23-inbox-parsing-and-syntax
plan: 01
subsystem: ui
tags: [parser, pydantic, fs-ui]

requires:
  - phase: 22-configuration-and-cli-modes
    provides: [append CLI subcommand structure]
provides:
  - Space-separated syntax parser for inbox files
  - ParsedCommand Pydantic model with group validation
affects: [24-fsui-orchestrator]

tech-stack:
  added: []
  patterns: [functional parser, Pydantic field validators]

key-files:
  created: [src/inbox/parser.py, tests/test_parser.py]
  modified: [src/core/schemas.py]

key-decisions:
  - "Used split(maxsplit=5) to reliably separate positional arguments from the title string without complex join logic."
  - "Stripping .pdf extension explicitly rather than using strip() for security."

patterns-established:
  - "Pure parser functions with no side effects (no LLM, no IO)."

requirements-completed: [FSUI-01] 

coverage:
  - id: D1
    description: "Parser correctly extracts 5 positional arguments and title"
    requirement: "FSUI-01"
    verification:
      - kind: unit
        ref: "tests/test_parser.py#test_parse_filename_syntax_valid"
        status: pass
    human_judgment: false
  - id: D2
    description: "Parser validates the group field restricts to 1-13, G, U"
    requirement: "FSUI-01"
    verification:
      - kind: unit
        ref: "tests/test_parser.py#test_parse_filename_syntax_group_validation"
        status: pass
    human_judgment: false

duration: 15 min
completed: 2026-07-20
status: complete
---

# Phase 23 Plan 01: Inbox Syntax Parser Summary

**Implemented space-separated filename parser and ParsedCommand Pydantic schema for FS-UI**

## Performance

- **Duration:** 15 min
- **Started:** 2026-07-20T15:37:00Z
- **Completed:** 2026-07-20T15:52:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Added `ParsedCommand` Pydantic model with custom validation for the `group` parameter
- Implemented `parse_filename_syntax` that cleanly handles space-separated syntax
- Verified edge cases like missing title and invalid formatting with `pytest`

## Task Commits

1. **Task 1: Add ParsedCommand schema** - `4762206` (feat)
2. **Task 2: Implement space-separated parser** - `ebfd5af` (feat)
3. **Task 3: Add unit tests for parser** - `dcec660` (test)

## Files Created/Modified
- `src/core/schemas.py` - Added `ParsedCommand` model
- `src/inbox/parser.py` - Added `parse_filename_syntax` function
- `tests/test_parser.py` - Added tests

## Decisions Made
- Used `split(maxsplit=5)` to reliably separate positional arguments from the title string without complex join logic.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Ready for plan 02 (Inferring missing data).
