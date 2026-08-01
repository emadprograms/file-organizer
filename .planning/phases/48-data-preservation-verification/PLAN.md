# Phase 48: Data Preservation & Verification Overhaul (Many-to-One)

## Goal
Fix the Reconcile module to correctly preserve Many-to-One document relationships (multiple JSON pages mapping to a single grouped shortcut) instead of deleting them. Add an Immutable Page Count check to the Verification module to crash the pipeline if page data is ever dropped.

## Strategy

1. **Fix `src/reconcile/core.py` (Many-to-One Matching)**
   - In `Phase 44: Verify Existing State vs Shortcuts`, the script currently matches physical shortcuts to `state_pages` using `if lnk in matched_lnks: continue`. This strictly enforces a 1-to-1 relationship and consumes the shortcut.
   - **Change needed:** We must allow multiple pages of the same grouped document to match against the *same* physical shortcut. 
   - Wait, if we just remove `if lnk in matched_lnks: continue`, we might accidentally double-count unrelated pages if they somehow have the same relative path? No, `expected_rel` is unique to the document group. 
   - Actually, just removing the exclusivity lock for pages that share the exact same `output_file` is the right approach. Let multiple pages point to the same `.lnk` without throwing them into `unmatched_pages`.

2. **Upgrade `src/core/verification.py` (Immutable Page Count)**
   - The Verifier currently just checks if links are broken. It has no idea if pages were silently deleted from `state.json`.
   - **Change needed:** Add a new test in `run_verification()`. 
   - It should calculate the original total pages. This can be done by looking at the total items in `cleaned_pages` in `state.json`.
   - It must then calculate the total `page_index` items in the final `manifest.per_page`.
   - If `len(cleaned_pages) != len(manifest.per_page)`, raise a loud, fatal `AssertionError` or return `False` and print a critical error. This prevents any phase from silently dropping pages.

3. **Testing**
   - Create `tests/test_reconcile_phase48.py`.
   - Mock a `state.json` that has a grouped document (3 pages pointing to the same `output_file`).
   - Run `run_reconcile_mode`.
   - Assert that the final state STILL has 3 pages for that document, and that they were not deleted.