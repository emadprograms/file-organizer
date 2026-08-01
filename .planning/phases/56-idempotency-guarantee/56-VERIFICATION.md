# Phase 56: Idempotency Guarantee - Verification

**Status:** Verified

## Verification Steps Performed

1. **Write Idempotency Tests**
   - We created `tests/test_reconcile_phase56.py`.
   - The test sets up a mock house structure with raw PDFs, ghost shortcuts, and tenants data.
   - It runs `run_reconcile_mode` the first time and asserts that the raw PDF is ingested and the ghost is adopted.
   - It captures the `state.json` file and records the `mtime` of all files in the directory.
   - It then executes `run_reconcile_mode` a second time (idempotent run).
   - It verifies that the operations report for the second run is completely zeroed out (0 raw PDFs ingested, 0 ghosts adopted, 0 file moves, 0 shortcuts repaired).
   - It performs a byte-for-byte exact comparison of the `state.json` before and after the second run, confirming zero metadata drift.
   - It ensures that the `mtime` of the physical files remains unchanged, proving that shortcuts are not needlessly re-written.

2. **Fix Unnecessary Shortcut Rewriting**
   - Replaced brute-force directory deletion of `[Timeline View]` with a smart logic that compares existing shortcuts by target (`batch_read_shortcut_targets`).
   - The timeline only issues new shortcut creations if the link doesn't exist or points to a different target. Unnecessary legacy or orphaned links are manually deleted.

3. **Verify Ghost and Raw Ingestion Stability**
   - Discovered that the internal `shortcuts` array within the `state.json` `DocumentGroup` was missing for newly ingested raw and ghost documents on the first run, leading to state mutation during the second run. 
   - We resolved this by recomputing the `g.shortcuts` mapping just before saving the `state.json`, ensuring the final generated list correctly embeds inside the `state.json` accurately from run 1.
   - Discovered that folder matching in `cleanup` deleted valid valid tenant directories because of the LRM (Left-To-Right Mark, `\u200E`) character. This was fixed by accurately passing the exact `allowed_dirs` map with the same invisible markers.

All `pytest` tests pass successfully, confirming that `run_reconcile_mode` behaves entirely idempotently across runs with no extra side-effects.
