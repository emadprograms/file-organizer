# Phase 32: Pipeline Migration - Summary

## Objective
Migrate the main pipeline output to use the new `00_Timeline_View/` folder logic and deprecate the physical `finalized.pdf`.

## Work Completed
- Added logic in `src/timeline/core.py` to create `00_Timeline_View/` and generate numbered shortcuts for each document processed, reflecting the chronological order.
- Removed the generation of `finalized.pdf` from `src/pipeline/runner.py`.
- Updated `src/watcher/orchestrator.py` to remove `finalized.pdf` reconstruction and TOC updating during the finalize append operations.
- Migrated tests in `tests/test_main_file_placement.py` and `tests/test_e2e_watcher.py` to assert the existence of `00_Timeline_View` instead of `finalized.pdf`.
- Removed deprecated `finalized.pdf` tests from `tests/test_finalize_append.py`.
- Updated `tests/test_reconcile_core.py` to remove dependency on `finalized.pdf` when testing ghost folder cleanup.

## Verification
- All 278 unit and E2E tests pass successfully (`pytest tests/`).
- The pipeline correctly produces timeline shortcuts and avoids monolithic PDF generation.

## Next Steps
Proceed to Phase 33 to implement Timeline Core Rebuild.
