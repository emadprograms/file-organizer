---
title: "Refactor main.py pipeline runner functions to src/pipeline/runner.py"
status: "complete"
---

# Summary

**Successfully refactored pipeline runner functions:**
- Created `src/pipeline/runner.py` and moved the 4 core pipeline pass functions (`run_cleaning_pass`, `run_grouping_pass`, `run_routing_pass`, `run_generation_pass`) to it.
- Cleaned up imports and function definitions in `src/main.py`, importing the runner functions from `src.pipeline.runner` instead.
- Refactored `src/fs_ui/orchestrator.py` to import the runner functions from `src.pipeline.runner`.
- Restored internal dynamic imports within the runner pass functions to ensure unit test patching works correctly.
- Updated mock patch targets in `tests/test_main_file_placement.py`, `tests/test_fs_ui_orchestrator.py`, and `tests/test_root_main_cli.py` to match the new imports.
- Ran the entire test suite via `pytest` and verified all 262 tests pass (260 passed, 2 skipped).
