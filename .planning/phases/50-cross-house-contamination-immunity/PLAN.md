# Phase 50: Cross-House Contamination Immunity - Plan

**Status:** Ready for execution

## Objective
Filter out "external shortcuts" (shortcuts pointing outside the current house's `.source_files` directory) during reconciliation, treating them as foreign objects to prevent cross-house state contamination.

## Plan Steps

1. **Update `src/reconcile/core.py` shortcut scanning logic**
   - **File:** `src/reconcile/core.py`
   - **Action:** Modify the loop that iterates over `physical_lnk_files` and resolves targets using `target_results`.
   - **Details:** 
     - After resolving `target_str` from `target_results`, check if `target_str` is within the current house's `.source_files` directory path.
     - You can use `str(source_dir.resolve())` as the prefix or a `Path(target_str).is_relative_to(source_dir)` check.
     - If the target path is NOT within the current house's `.source_files`, log a warning/info message and `continue` (skipping the shortcut entirely).
     - This ensures that shortcuts from other houses or the Desktop are completely ignored by the reconciler.

2. **Add a test case for external shortcuts**
   - **File:** `tests/test_reconcile.py` (or the relevant reconciliation test file).
   - **Action:** Add a test that creates a shortcut in the house's target directory that points to an external file (e.g., a dummy vault file in a temporary folder outside the house).
   - **Details:** Verify that the reconciler successfully ignores the external shortcut, doesn't crash, and doesn't modify the state based on it.

## Verification
- Run `pytest` to ensure all tests pass.
- Verify that a shortcut placed in one house's folder pointing to a different house's vault is ignored and does not alter the target house's `state.json`.
