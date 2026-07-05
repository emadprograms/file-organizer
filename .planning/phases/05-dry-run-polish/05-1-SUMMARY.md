---
phase: "05"
plan: "1"
subsystem: cli-output
tags: [dry-run, visualizer, rich, cli]
dependency_graph:
  requires: []
  provides: [dry-run-flag, visualizer-module]
  affects: [organize.py, organizer.py, visualizer.py]
tech_stack:
  added: [rich.console, rich.tree, rich.table]
  patterns: [guard-clause dry_run, conditional-file-write]
key_files:
  created:
    - src/processing/visualizer.py
  modified:
    - src/organize.py
    - src/processing/organizer.py
    - tests/test_pipeline_pass2.py
    - tests/test_routing.py
decisions:
  - "--dry-run reads existing checkpoints (cleaned.json/grouped.json) to skip LLM calls if available"
  - "Visualizer is invoked after reconciliation to ensure accurate per_page data for tree rendering"
  - "Windows UTF-8 reconfigure applied before validate_environment to prevent Arabic UnicodeEncodeError"
metrics:
  duration: "~20 minutes"
  completed: "2026-07-05"
  tasks_completed: 4
  files_modified: 5
status: complete
---

# Phase 05 Plan 1: Core Dry Run Support & CLI Output Summary

**One-liner:** `--dry-run` flag with rich Tree/Table visualization and checkpoint-aware skipping for the full pipeline

## What Was Built

Implemented end-to-end `--dry-run` support across the pipeline so users can preview the entire folder structure and output file plan without writing any PDFs or JSON files to disk.

### Task 1 — `organizer.py`: `dry_run` parameter
- Added `dry_run: bool = False` to `FileOrganizer.organize()` and `run_reconciliation()`
- `os.makedirs()` and `extract_pdf_segment()` are wrapped in `if not dry_run:` blocks
- Manifest writing in `run_reconciliation` is guarded similarly
- Commit: `dfbc3d3`

### Task 2 — `organize.py`: `--dry-run` CLI flag
- Added `--dry-run` argument with `action="store_true"` to `get_parser()`
- Windows-aware UTF-8 reconfigure with fallback warning if encoding is not UTF-8
- Commit: `425bc09`

### Task 3 — `organize.py`: Checkpoint skipping logic
- When `--dry-run` is active, `cleaned.json` and `grouped.json` are loaded from disk (bypassing LLM calls) if they exist
- When running dry-run, neither checkpoint file is written
- `manifest.json` writing is bypassed via `run_reconciliation(dry_run=True)`
- Commit: `425bc09` (same commit as Task 2, logically grouped)

### Task 4 — `visualizer.py`: Rich visualization module
- Created `src/processing/visualizer.py` with `Visualizer` class
- `print_summary()` renders a `rich.table.Table` (summary metrics) and a `rich.tree.Tree` (House→Tenant→Category→PDF hierarchy)
- Invoked from `organize.py` `main()` when `args.dry_run` is `True`
- Commit: `bed875d`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test regressions from --dry-run addition**
- **Found during:** Post-implementation test run
- **Issue:** `test_pipeline_pass2.py` tests mock `argparse.ArgumentParser.parse_args` with `SimpleNamespace` objects missing the `dry_run` attribute, causing `AttributeError: 'types.SimpleNamespace' object has no attribute 'dry_run'`. `test_routing.py` used `Path("dummy_out")` (relative) as `output_base_dir`, which failed after `target_dir.resolve()` made the resolved path absolute while `output_base_dir` stayed relative.
- **Fix:** Added `dry_run=False` to all `SimpleNamespace` mock args; changed routing tests to use `tmp_path` (absolute pytest fixture)
- **Files modified:** `tests/test_pipeline_pass2.py`, `tests/test_routing.py`
- **Commit:** `734a489`

## Verification

- `python src/organize.py --help` shows `--dry-run` ✅
- All 5 previously-failing tests now pass ✅
- `test_cli.py` (8 tests) all pass ✅

## Self-Check: PASSED

- [x] `src/processing/visualizer.py` exists
- [x] `--dry-run` in `get_parser()` — confirmed via `--help`
- [x] `dry_run` param in `organize()` and `run_reconciliation()` — confirmed in source
- [x] All commits verified in git log (dfbc3d3, 425bc09, bed875d, 734a489)
