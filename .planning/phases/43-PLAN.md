# Phase 43: Ghost File Adoption & Raw PDF Ingestion

## Goal
Implement the ability for the reconciler to adopt ghost shortcuts and ingest raw PDFs directly from categorized folders, updating `state.json` accordingly.

## Strategy
1. **Raw PDF Ingestion (REQ-03)**
   - In `run_reconcile_mode` in `src/reconcile/core.py`, before processing shortcuts, scan for `*.pdf` files in the `target_dir` (excluding `.source_files` and `[Timeline View]`).
   - For each raw PDF:
     - Generate a new `vault_id` using `uuid.uuid4().hex`.
     - Move the PDF to `.source_files/vault/doc_{vault_id}.pdf`.
     - Create a `.lnk` shortcut at the original location pointing to the vault PDF.
     - Extract a date from the filename (using a date regex or falling back to a default like "nodate").
     - Create `PageData` and `DocumentGroup` entries and a `per_page` manifest entry in the unified state data, marked as `user_locked: True`.
2. **Ghost Shortcut Adoption (REQ-01)**
   - When scanning `physical_lnk_files`, if a shortcut points to a `doc_{vault_id}.pdf` in the vault but this `vault_id` is missing from `state.json` (the `vault_id_to_page` map), this is a ghost shortcut.
   - For each ghost shortcut:
     - Verify the vault PDF exists. If it does not, skip (this would be an orphan shortcut, we might just ignore or log a warning).
     - Extract a date from the shortcut's filename.
     - Create `PageData`, `DocumentGroup`, and `per_page` entries in the unified state data.
     - Mark as `user_locked: True`.
3. **Integration**
   - Ensure the newly adopted files are appended to the lists of pages, groups, and `old_per_page` list so that they participate in tenant-based moves if necessary, but since they are `user_locked`, they will stay in their current folder.
4. **Testing**
   - Write comprehensive `pytest` tests in `tests/test_reconcile_phase43.py` to validate raw PDF ingestion and ghost shortcut adoption.
