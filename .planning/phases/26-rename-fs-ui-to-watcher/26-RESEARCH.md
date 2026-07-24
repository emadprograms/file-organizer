# Phase 26: Rename `fs_ui/` to `watcher/` - Research

**Date:** 2026-07-24
**Status:** Completed
**Domain:** Architectural Cleanup (ARCH-02)

## Executive Summary
Phase 26 renames the `fs_ui/` directory and its associated test files to `watcher/`. The name `watcher` accurately reflects the package's responsibilities: file watching, process locking, and event-driven orchestration.

## Audit Results
- `src/fs_ui/` contains `__init__.py`, `lock.py`, and `orchestrator.py`.
- Test files needing renaming: `test_e2e_fs_ui.py`, `test_fs_ui_append_mock.py`, `test_fs_ui_lock.py`, `test_fs_ui_orchestrator.py`.
- References to `fs_ui` exist in `src/main.py`, `tests/test_pipeline_e2e.py`, `tests/test_root_main_append_mode.py`, and the renamed test files.
- The renaming requires updates to Python module paths (`src.fs_ui` -> `src.watcher`) and patch strings in mocks.
