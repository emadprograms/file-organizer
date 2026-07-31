# Phase 33: Bidirectional Reconciliation Engine - Plan

## Step 1: Scan Physical Shortcuts (RECON-01, RECON-02, RECON-07)
- Add a function `scan_physical_shortcuts(house_dir, routed_data)` in `src/reconcile/core.py`.
- This function will scan all `.lnk` files in the tenant subdirectories (excluding `.source_files`).
- Read the target of each shortcut (or just match by filename/vault UUID). We need to extract the `vault_id` from the shortcut target path or the filename.
- Compare the physical location (tenant/topic folder) of each shortcut with the `target_folder` in `routed_data["per_page"]`.
- If a shortcut is missing, mark it as deleted (log warning).
- If a shortcut is in a different folder, flag it as manually moved.

## Step 2: Lock Manually Moved Shortcuts (RECON-03, RECON-04)
- For any shortcut that was manually moved, update the corresponding entry in `routed_data["per_page"]` with the new `target_folder` and `output_file`, and set `user_locked = True`.
- Update the `DocumentGroup` (in `_2_grouped.json`) and `PageData` (in `_1_cleaned.json`) to reflect `user_locked = True` so that future AI re-routing or tenant config updates skip them.

## Step 3: Update `reconcile --tenants` (RECON-05)
- In `run_reconcile_mode`, when applying updated timelines from `_tenants.yaml`, ONLY apply changes to `DocumentGroup` and `PageData` that DO NOT have `user_locked == True`.
- Only update `output_file` and move physical shortcuts if `user_locked` is False.

## Step 4: Regenerate `00_Timeline_View/` (RECON-06)
- After all reconciliation logic completes (moves, locks, tenant updates), completely wipe the `00_Timeline_View/` folder and rebuild it based on the updated `routed_data["per_page"]`.
- The Timeline view should accurately reflect the new locations and chronological order of all documents (locked and unlocked).

## Step 5: Update Tests
- Write unit tests for `scan_physical_shortcuts`.
- Write end-to-end tests for locking manually moved shortcuts.
- Update `test_reconcile_core.py` to cover `user_locked` and Timeline view regeneration.
