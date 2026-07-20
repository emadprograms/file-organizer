---
phase: 22-configuration-and-cli-modes
plan: 02
subsystem: cli
tags: [argparse, filelock, cli]

# Dependency graph
requires:
  - phase: 22-configuration-and-cli-modes
    provides: [Configuration management and Pydantic validation]
provides:
  - CLI argument routing with subparsers (create, append)
  - Process-exclusive lock mechanism for the listener
affects: [23-fs-ui, 24-listener-loop]

# Tech tracking
tech-stack:
  added: [filelock]
  patterns: [CLI Parser pattern, Process Exclusive Lock]

key-files:
  created: [tests/test_listener_lock.py]
  modified: [src/main.py, requirements.txt, tests/test_main_cli.py]

key-decisions:
  - "Argparse subparsers route execution to either the history-building logic or the listener stub."
  - "The listener stub uses `filelock.FileLock` with timeout=0 to ensure mutual exclusion gracefully."

patterns-established:
  - "Pattern 2: Process Exclusive Lock"

requirements-completed: [CONF-02, CONF-03]

coverage:
  - id: D1
    description: "create subparser enforces strict path boundaries against config.areas_root_path"
    requirement: "CONF-02"
    verification:
      - kind: unit
        ref: "tests/test_main_cli.py::test_main_create_boundary_check"
        status: pass
    human_judgment: false
  - id: D2
    description: "append mode implements filelock and exits cleanly on conflict"
    requirement: "CONF-03"
    verification:
      - kind: unit
        ref: "tests/test_listener_lock.py::test_run_append_mode_already_locked"
        status: pass
    human_judgment: false

# Metrics
duration: 6 min
completed: 2026-07-20
status: complete
---

# Phase 22 Plan 02: CLI Modes and Concurrency Summary

**Refactored CLI with `argparse` subparsers (`create` and `append`) and implemented lockfile mutual exclusion for the upcoming listener loop.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-20T12:31:00+03:00
- **Completed:** 2026-07-20T12:37:00+03:00
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Refactored `src/main.py` CLI to support explicit `create` and `append` commands using `argparse.ArgumentParser.add_subparsers`.
- `create` mode dynamically enforces a strict path constraint checking that the target directory lies within `config.areas_root_path`.
- Implemented `run_append_mode` stub using `filelock.FileLock` to prevent concurrent listener instances from running via `.inbox.lock`.
- Updated test coverage for argument parsing routing and lock mechanism success/failure states.

## Files Created/Modified
- `requirements.txt` - Added `filelock` dependency.
- `src/main.py` - Replaced single command with `create` and `append` subparsers, added `run_append_mode`.
- `tests/test_main_cli.py` - Updated existing pipeline tests to use the `create` subcommand, and mocked `AppConfig`.
- `tests/test_listener_lock.py` - Full coverage for the `FileLock` logic and listener lifecycle.

## Decisions Made
- `filelock` is used instead of primitive `os.open` mechanisms to prevent lockfile staleness upon unexpected exit.
- Pydantic's `AppConfig` is instantiated early within `main()` so that path validations can execute before deferring to pipeline logic.

## Deviations from Plan

None - plan executed strictly.

## Issues Encountered
None. The test mocking required a slight adjustment to mock `AppConfig` correctly instead of `src.main.AppConfig`, but no architectural issues.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The CLI is fully structured to hand off to the File-System UI listener (Phase 23/24).
- `run_append_mode` is ready to be fleshed out with actual directory observation loops.
