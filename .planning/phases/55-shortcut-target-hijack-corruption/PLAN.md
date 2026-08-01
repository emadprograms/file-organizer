# Phase 55 Plan: Shortcut Target Hijack / Corruption

## Objective
Prevent the reconciler from mistakenly treating modified or corrupted `.lnk` files (shortcuts pointing to wrong vault IDs or external targets) as user deletions, which currently results in the permanent trashing of the associated Vault PDF. Instead, the system should actively detect hijacked/broken shortcuts based on `state.json` and auto-repair them to point back to the correct vault ID.

## Core Problem
Currently in `src/reconcile/core.py`, if a shortcut's target is changed to point outside the vault or to a different vault document, the initial scan ignores it or associates it with the wrong vault ID. When iterating through `vault_id_to_pages`, if no valid physical shortcuts are found for a given `vault_id`, the system assumes the user intentionally deleted the document and trashes the Vault PDF (`deleted_vault_ids.add(vault_id)`). 
If the shortcut file physically exists at the expected `output_file` path but has a corrupted/hijacked target, we must intervene before deletion.

## Implementation Steps

### Step 1: Track Known Output Paths & Identify Hijacked Shortcuts
In `src/reconcile/core.py`, we need to determine if a missing shortcut is truly deleted from the filesystem or just hijacked/corrupted.

**Action:**
- Extract all known shortcut relative paths from `state.json` into a lookup map (e.g., `expected_shortcut_paths`) mapping the expected physical path (relative to the house directory) to its intended `vault_id`.
- Add a new report counter: `report["shortcuts_repaired"] = 0`.
- Iterate through `physical_lnk_files`. For each file, compute its relative path. If this path matches an entry in `expected_shortcut_paths` but its target is invalid, broken, external, or points to the wrong `vault_id`, tag it as "hijacked".

### Step 2: Prevent Vault PDF Deletion & Inject Repaired Shortcuts
Modify the deletion detection logic:

**Action:**
- When iterating over `vault_id_to_pages` and checking if `vault_id not in seen_vault_ids`:
  - Before concluding it's a "user deletion", check if any of the expected `output_file` paths for this `vault_id` physically exist as `.lnk` files on disk (even if they were ignored or assigned to a different `vault_id` in the initial target scan).
  - If a physical `.lnk` file exists at the expected path, **do not** add the `vault_id` to `deleted_vault_ids`.
  - Instead, mark this as an auto-repair event (`report["shortcuts_repaired"] += 1`), log a clear message (`logger.info("Auto-repairing hijacked shortcut...")`), and manually append the physical `lnk_path` to `physical_lnk_by_vault[vault_id]`.
  - Ensure that if the shortcut was miscategorized under a different `vault_id`, it is removed from that incorrect bucket to prevent cross-contamination.

### Step 3: Leverage Existing Rewrite Logic
The existing architecture already rewrites all categorized shortcuts at the end of the reconciliation loop (`shortcuts_to_rewrite`). 

**Action:**
- By ensuring the hijacked `.lnk` file is correctly mapped back to its original `vault_id` in `physical_lnk_by_vault`, it will flow through the rest of the script normally.
- The existing `batch_create_shortcuts` at the end of the script will automatically overwrite the corrupted `.lnk` file with the correct absolute target path pointing to the proper vault PDF.

### Step 4: Add Verification Rules
Update `src/core/verification.py` to flag any shortcut that points to the wrong vault ID.

**Action:**
- Currently, `verification.py` might be checking if shortcuts point to the vault. Ensure it explicitly cross-references `state.json` to verify that each shortcut's target strictly matches the `vault_id` it is assigned to.
- If it doesn't match, the verifier should report a hijack/corruption warning.

## Success Criteria
- [ ] A shortcut pointing to a random external file is auto-repaired, and its vault PDF is **not** deleted.
- [ ] A shortcut pointing to the wrong vault PDF is auto-repaired to its correct vault PDF.
- [ ] The reconciliation report logs the exact number of `shortcuts_repaired`.
- [ ] Automated tests confirm these resilience scenarios work as expected.
