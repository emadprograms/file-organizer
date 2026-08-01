# Phase 44: User Deletion & Orphan Cleanup Plan

## Goal
Implement logic in the reconciler to detect when a user deletes a shortcut, remove it from `state.json`, and move the orphaned vault PDF to `.source_files/.trash/` for safe recovery.

## Strategy
1. **Detect Deleted Shortcuts (Orphan Detection in State)**
   - In `run_reconcile_mode`, we currently detect missing shortcuts with:
     ```python
     for vault_id, p in list(vault_id_to_page.items()):
         if vault_id not in seen_vault_ids:
             logger.warning(f"Shortcut for vault_id {vault_id} was deleted or missing.")
     ```
   - Enhance this logic: if a `vault_id` from the state is NOT found among physical shortcuts (and is not an ingested raw PDF from this run), it indicates the user deleted the shortcut.
   - For these deleted shortcuts:
     - Remove the `per_page` entry from `routed_data["per_page"]`.
     - Remove the corresponding `PageData` and `DocumentGroup` entries from `pages` and `groups` based on `page_index`.
     - Move the `doc_{vault_id}.pdf` file from the vault to `.source_files/.trash/doc_{vault_id}.pdf`.

2. **Detect Orphaned Vault PDFs (Orphan Detection on Disk)**
   - Scan `.source_files/vault/` for all `doc_{vault_id}.pdf` files.
   - If a vault PDF's `vault_id` is not present in the updated `state.json` manifest (`per_page`), it is an orphan (perhaps leftover from an old error).
   - Move these orphan PDFs to `.source_files/.trash/` as well.

3. **Re-index Pages and Groups**
   - After removing entries from `pages` and `groups`, the `original_index` / `page_index` fields might have gaps.
   - The reconciliation should safely remove them, though re-indexing everything might be complex if there are dependencies. We will just remove them and ensure they don't appear in the new `per_page` list. (Wait, `per_page` references `page_index`. If we delete a page in the middle, `page_index` across other `per_page` entries will no longer match the array indices in `pages` unless we re-index).
   - Better approach: rebuild `pages`, `groups`, and `per_page` lists from scratch excluding the deleted ones, and update the indices.
   - Wait, `old_per_page` processing maps by `p["page_index"]`. If we remove the item from `old_per_page` and `vault_id_to_page`, we should re-index carefully. We'll assign a new sequential index.

4. **Testing**
   - Write tests in `tests/test_reconcile_phase44.py`.
   - Test user deletion: mock a state with a shortcut, delete the physical shortcut, run reconciliation, verify state is cleaned up and vault PDF is trashed.
   - Test orphan disk PDF: mock a vault PDF without state, run reconciliation, verify it is moved to `.trash/`.
