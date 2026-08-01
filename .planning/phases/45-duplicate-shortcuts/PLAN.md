# Phase 45: Duplicate Shortcuts & Renamed Shortcuts Plan

## Goal
Update the reconciler to handle 1-to-many relationships (duplicate shortcuts pointing to the same vault PDF) and detect when the user renames a shortcut, updating `state.json` appropriately.

## Strategy
1. **Handle Duplicate Shortcuts (REQ-04)**
   - Currently, in `run_reconcile_mode`, we map `vault_id_to_page` as a simple dictionary. If a `vault_id` appears multiple times, or if a user copies a shortcut, we might override entries or miss them.
   - Wait, `per_page` handles multiple pages with different indices, but if a single page is copied, it points to the same vault PDF. 
   - When scanning `physical_lnk_files`, we find all occurrences of a `vault_id`. 
   - Update `vault_id_to_page` to be a mapping of `vault_id -> list[dict]` (i.e. all tracked paths for that vault PDF).
   - If we find a `vault_id` that is already in `state.json`, but the physical shortcut doesn't match any of its known `output_file` paths, it could be a renamed shortcut or a copied shortcut.
   
2. **Handle Renamed Shortcuts (REQ-05)**
   - If a `vault_id` has exactly 1 tracked `per_page` entry, but we find exactly 1 physical shortcut for it with a *different* name or folder, we can treat it as moved/renamed. Update the `output_file`, `brief_arabic_title`, and set `user_locked: true`.
   - If the user *copied* the shortcut (so there are >1 physical shortcuts), we have to be careful. The original one might be untouched, while the new one is an "adoption" (effectively the same page, but we should create a new `per_page` entry with the same `vault_id`?). Wait, if `state.json` has 1 entry, and we find 2 physical shortcuts, the second one is a ghost shortcut that points to the same vault PDF! Our Phase 43 logic already adopts ghost shortcuts! 
   - Wait! Phase 43 ghost shortcut adoption says: "If vault_id not in vault_id_to_page". BUT what if it IS in `vault_id_to_page`, but the relative path doesn't match? We just treated it as a move!
   - In Phase 43, `p = vault_id_to_page[vault_id]` assumes 1-to-1. It then says "if rel_path != expected_rel: update p". So if there are two shortcuts, it updates `p` with the first one, then updates `p` AGAIN with the second one! This means it just overwrites the state with the last shortcut it sees, and the other physical shortcut is ignored (and during generation, it might only generate one).

3. **Algorithm for Phase 45**
   - Group physical shortcuts by `vault_id`.
   - Map state `per_page` entries by `vault_id` (this is `vault_id_to_page`, which becomes `vault_id_to_pages`: `dict[str, list[dict]]`).
   - For each `vault_id`:
     - If it's a ghost (not in state), adopt all physical shortcuts as new pages (handled similarly to Phase 43 but loop over all).
     - If it IS in state:
       - Attempt to match physical shortcuts to state entries by exact `output_file` path.
       - For physical shortcuts that don't match, and state entries that weren't matched:
         - If the number of unmatched physical == number of unmatched state entries, we can assume they are renames/moves 1-to-1.
         - If unmatched physical > unmatched state: some are copies. Adopt the extras as new `per_page` entries!
         - If unmatched physical < unmatched state: some were deleted. Delete the extras!
   - Apply `user_locked: true` to any matched pair where the name/path changed.

4. **Testing**
   - Write tests in `tests/test_reconcile_phase45.py`.
   - Test renamed shortcut (1-to-1 match but different name).
   - Test duplicate shortcut (1 state entry, 2 physical shortcuts -> should adopt the second as a duplicate reference).
