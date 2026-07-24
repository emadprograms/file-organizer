# Phase 29: Audit Test Mock Patch Targets - Research

**Date:** 2026-07-24
**Status:** Completed
**Domain:** Architectural Cleanup (ARCH-05)

## Executive Summary
Phase 29 audits and corrects test mock patch targets to ensure they are patched at the import site instead of the definition site, especially focusing on `src.main.*` and `src.pipeline.*`.

## Audit Results
- `tests/test_root_main_cli.py` patched `src.pipeline.pipeline.Pipeline` and `src.timeline.FileOrganizer` when testing `main.py`.
- `src/main.py` does not import `Pipeline` or `FileOrganizer` after the runner extraction refactor; instead, it imports and uses `run_cleaning_pass`, `run_grouping_pass`, `run_routing_pass`, and `run_generation_pass` from `src.pipeline.runner`.
- By updating `test_root_main_cli.py` to patch `src.main.run_cleaning_pass`, etc., we properly intercept the functions where they are imported and called in `main.py`, fully resolving the bad mock target issue.
