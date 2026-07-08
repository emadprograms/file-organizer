# Summary: Global Logger Migration - Wave 2

## Objective
Convert all system telemetry `print()` statements in the `src/` directory to appropriate logging levels.

## Changes
- **src/core/config.py**: 
  - Added `import logging`.
  - Initialized `logger = logging.getLogger(f"file_organizer.{__name__}")`.
  - Replaced `print(f"Warning: ...")` in `record_successful_call` with `logger.warning()`.
- **src/organize.py**:
  - Replaced terminal encoding warnings in `main()` with `logger.warning()`.
  - Replaced `print` calls in exception blocks with `logger.error()` and `logger.exception()`.
  - Removed redundant `if 'logger' in locals():` checks since `logger` is a global module-level object.

## Verification
- Ran `grep -r "print(" src/ | grep -v "console.print"`.
- Result: 0 matches.
- All remaining `print` calls are `console.print` (UI output).

## Status
- [x] Task 1: Convert Telemetry Prints to Loggers
- [x] Task 2: Final Print Purge Verification
