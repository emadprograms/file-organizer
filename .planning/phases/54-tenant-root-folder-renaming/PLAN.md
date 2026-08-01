# Phase 54: Tenant Root Folder Renaming - Plan

## 1. Context & Objective
The user modifies top-level tenant folder names (e.g., from `Tenant A (2020 - 2021)` to `My Custom Folder`).
The system must safely handle this during reconciliation and generation:
- The Reconciler scans the renamed folder and maps the shortcuts inside it to the state because they still point to valid vault files.
- The Generator rebuilds the output structure based on `tenants.yaml`. It creates the canonical folder `Tenant A (2020 - 2021)`.
- The Generator must identify that `My Custom Folder` is an old/renamed output folder and **DELETE** it to prevent leaving orphaned folders behind.

## 2. Technical Approach

### Reconciler Updates (`src/reconcile/core.py` or equivalent)
- Currently, the reconciler discovers shortcuts inside `My Custom Folder`. Since they point to valid vault IDs, the state is updated, and the files are successfully mapped.
- Ensure that no proactive `os.rename` or physical folder correction occurs during the discovery phase (overriding the previous strategy in `54-CONTEXT.md`). Let the shortcuts be adopted from their current path.

### Generator Updates (`src/timeline/phase.py` / `src/timeline/core.py` / `src/reconcile/core.py`)
- The generation phase creates the canonical folders based strictly on `tenants.yaml`.
- During cleanup (at the end of generation or reconciliation), the generator must scan the top-level directories in `target_dir`.
- Any top-level directory that is:
  1. Not `.source_files`
  2. Not `[Timeline View]`
  3. Not one of the canonical tenant folders just generated
  4. Contains only `.lnk` files pointing to the vault (or is completely empty)
  Must be considered an orphaned/renamed legacy folder and be recursively deleted using `shutil.rmtree()`.
- **Safety measure**: Care must be taken not to delete user directories containing unmanaged physical files (e.g., if the user dropped raw PDFs into `My Custom Folder`, they should ideally be adopted first, but if physical non-shortcut files remain, the folder should not be blindly deleted to prevent data loss).

## 3. Implementation Steps

1. **Remove Proactive Renaming in Reconciler (if any):**
   - Ensure `src/reconcile/core.py` does not attempt to proactively rename physical folders back to canonical names. It should simply parse shortcuts regardless of their parent folder name.

2. **Implement Cleanup Logic in Generator:**
   - In the generation phase (or at the end of `run_reconcile_mode`), compile a `Set` of "allowed" top-level directories: canonical tenant folders from YAML + `.source_files` + `[Timeline View]`.
   - Iterate over all actual top-level directories in `target_dir`.
   - If a directory is not in the "allowed" list:
     - Check its contents. If it contains only shortcuts (which have already been parsed and generated in the canonical folder) or is empty, delete it via `shutil.rmtree()`.
     - Log the deletion: `Deleted orphaned/renamed legacy folder: {dir_name}`.

3. **Update State Tracking:**
   - Ensure that the state assignment perfectly aligns shortcuts from the renamed folder back to the canonical folder using the tenant ID mapping, so no data is lost.

4. **Add Tests:**
   - Add a test case in `tests/test_reconcile.py` simulating a user renaming a canonical folder to `My Custom Folder`, running reconciliation, and asserting that `My Custom Folder` is deleted and the canonical folder is restored with valid shortcuts.
