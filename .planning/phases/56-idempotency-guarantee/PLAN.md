# Phase 56: Idempotency Guarantee - Plan

**Status:** Ready for execution

## Objective
Ensure that running the reconciler multiple times on the same state produces absolutely zero side-effects. This includes verifying that ghost adoption, raw PDF ingestion, and folder reconciliation are fully idempotent and that metadata is completely stable across runs without unnecessary file timestamp updates.

## Plan Steps

1. **Write Idempotency Tests**
   - **File:** `tests/test_reconcile_phase56.py`
   - **Action:** Create integration tests that verify idempotency.
   - **Details:**
     - Setup a house with raw PDFs, ghost shortcuts, and a normal document.
     - Run `run_reconcile_mode`. Verify standard first-run actions (ghost adopted, raw PDF ingested, timelines created).
     - Capture the exact state of `state.json` and a snapshot of file modification times across the house folder.
     - Run `run_reconcile_mode` a second and third time.
     - Verify that the reconciler report on runs 2 and 3 shows 0 operations across the board (0 ghosts adopted, 0 raw PDFs ingested, 0 moves, 0 shortcuts repaired).
     - Verify that `state.json` content remains 100% identical byte-for-byte.
     - Verify that the physical `.lnk` and `.pdf` files are not modified/re-written (their `mtime` should remain unchanged).

2. **Fix Unnecessary Shortcut Rewriting**
   - **File:** `src/reconcile/core.py`
   - **Action:** Stop blindly deleting and recreating all shortcuts in `[Timeline View]` and only create/update `shortcuts_to_rewrite` if they actually changed.
   - **Details:**
     - For `shortcuts_to_rewrite`: Use `batch_read_shortcut_targets` on the existing shortcuts first. Only add them to the rewrite list if the `.lnk` file doesn't exist, or if its target does not exactly match `vault_pdf`.
     - For `[Timeline View]`: Remove `shutil.rmtree(str(timeline_dir))`. Instead, read existing shortcuts in that directory. Create/update the required ones, and delete the ones that are no longer needed, bypassing any writes if the existing shortcut has the exact same name and target.

3. **Verify Ghost and Raw Ingestion Stability**
   - **File:** `src/reconcile/core.py`
   - **Action:** Ensure there are no metadata drifts (such as dates getting repeatedly altered or UUIDs leaking).
   - **Details:** 
     - Confirm that after a ghost is adopted, its `vault_id` correctly associates with its pages in `state.json` so the next run skips it. (Currently believed to be correct, verify through the test).
     - Ensure no side effects leak from `valid_folder_names_set` or `unmatched_pages` mapping if everything is in place.

## Verification
- Run `pytest tests/test_reconcile_phase56.py` to ensure tests pass and strictly enforce zero file modification times on the second run.
- Check that running the reconciler via CLI twice results in a completely clean second report.
