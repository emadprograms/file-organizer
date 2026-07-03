---
phase: 01-foundation-infrastructure
plan: 03
subsystem: CLI
tags: [argparse, validation, llm]

requires: []
provides:
  - CLI script that accepts target directory and validates inputs
  - Validation of exactly one `_categorized.pdf` and `_report.json`
  - Extraction of house ID
  - LLMClient instantiation and logger setup
affects: []

tech-stack:
  added: [argparse, dotenv]
  patterns: [CLI script structure, fail-fast validation]

key-files:
  created: [src/organize.py, tests/test_cli.py]
  modified: []

key-decisions:
  - "Used standard argparse for CLI as requirements are simple"
  - "Mocked load_dotenv in tests to prevent side effects from actual .env file"
  - "Added path adjustment to sys.path so src module is resolvable when run directly"

patterns-established:
  - "Fail fast validation on startup"

requirements-completed: [INIT-01, INIT-02, INIT-03, INIT-04, INIT-05, INIT-06, INIT-07]

coverage:
  - id: D1
    description: "CLI parses target_dir and --model correctly"
    requirement: INIT-01
    verification:
      - kind: unit
        ref: "tests/test_cli.py#test_parser_default_model"
        status: pass
      - kind: unit
        ref: "tests/test_cli.py#test_parser_custom_model"
        status: pass
    human_judgment: false
  - id: D2
    description: "CLI enforces GEMINI_API_KEY presence"
    requirement: INIT-04
    verification:
      - kind: unit
        ref: "tests/test_cli.py#test_validate_environment_missing_key"
        status: pass
    human_judgment: false
  - id: D3
    description: "Target directory validation asserts file existence, matching IDs, extracts house ID, and creates output dir"
    requirement: INIT-02
    verification:
      - kind: unit
        ref: "tests/test_cli.py#test_validate_target_directory_success"
        status: pass
      - kind: unit
        ref: "tests/test_cli.py#test_validate_target_directory_missing_pdf"
        status: pass
      - kind: unit
        ref: "tests/test_cli.py#test_validate_target_directory_mismatch_id"
        status: pass
    human_judgment: false
  - id: D4
    description: "Main pipeline properly instantiates LLMClient and logger"
    verification:
      - kind: unit
        ref: "tests/test_cli.py#test_main_success"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-07-03
status: complete
---

# Phase 01 Plan 03: CLI Entry Point Summary

**CLI entry point with argparse, fast-fail environment validation, and dependency instantiation.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-07-03T20:03:47Z
- **Completed:** 2026-07-03T20:08:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Implemented `organize.py` CLI script with `argparse`.
- Added strict startup environment validation for `GEMINI_API_KEY` using `dotenv`.
- Built robust target directory validation that guarantees the existence of a matching `*_categorized.pdf` and `*_report.json`.
- Safely extracts the House ID from filenames.
- Connected `LLMClient` and logging setup to the main execution flow.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create `src/organize.py` with `argparse` and env validation** - `25d0b73` (feat)
2. **Task 2: Implement `validate_target_directory(target_dir: Path)`** - `b264ccd` (feat)
3. **Task 3: Instantiate logger and LLMClient in main** - `bc57b50` (feat)

## Files Created/Modified
- `src/organize.py` - Core entry point script for the application.
- `tests/test_cli.py` - Comprehensive unit test coverage for the CLI parsing and validation logic.

## Decisions Made
- Adjusted `sys.path` dynamically in `organize.py` to allow execution via `python src/organize.py` without package resolution errors.
- Added comprehensive unit testing with `pytest` utilizing `unittest.mock` to isolate dependencies like the `.env` file and logging side effects.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- Foundation is completely established.
- Ready for Phase 2: Document Cleaning and LLM grouping logic.

## Self-Check: PASSED
