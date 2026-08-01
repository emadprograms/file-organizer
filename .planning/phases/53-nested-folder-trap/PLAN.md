# Phase 53: Nested Folder Trap - Plan

**Status:** Ready for execution

## Objective
Support robust handling of nested folder structures inside tenant directories. When a user creates arbitrary subfolders and moves shortcuts into them, the system must track the exact nested hierarchy (e.g., `01_Cat/My Custom Subfolder/doc.lnk`) as the `target_folder`, log it accurately in `state.json`, and regenerate the shortcut at that exact nested path. It must NOT flatten the nested folders back to the root category.

## Plan Steps

1. **Verify and Update Relative Path Extraction**
   - **File:** `src/reconcile/core.py` (or relevant reconciliation module).
   - **Action:** Ensure `target_folder` is extracted using the full relative path from the target directory (`Path(rel_path).parent.as_posix()`). 
   - **Details:** The reconciler uses `Path.rglob('*.lnk')` and calculates relativity out of the box, but we must guarantee that arbitrary subfolders are persisted exactly as-is in `state.json` without any flattening or root-category normalization.

2. **Update Shortcut Regeneration Logic**
   - **File:** `src/reconcile/core.py` (or relevant generation module).
   - **Action:** Ensure that when regenerating shortcuts from `state.json`, the full `target_folder` path is used.
   - **Details:** Call `Path.mkdir(parents=True, exist_ok=True)` on the destination folder before creating the `.lnk` file to ensure any dynamically tracked subfolders are successfully recreated if they were deleted.

3. **Update Timeline Location Tags**
   - **File:** `src/reconcile/timeline.py` (or relevant timeline module).
   - **Action:** Update the generation of the timeline shortcut filename.
   - **Details:** When parsing the location tag from the `target_folder`, use the deepest parent folder's name rather than the root category name (e.g., if the path is `01_Cat/My Custom Subfolder`, the tag should be `[My Custom Subfolder]`).

4. **Add Comprehensive Tests for Nested Hierarchy**
   - **File:** `tests/test_reconcile.py` (or related test suite).
   - **Action:** Add test cases asserting correct nested behavior.
   - **Details:** 
     - Create a mock state with a deeply nested shortcut (`Tenant A/01_Cat/Sub/Deep/doc.lnk`).
     - Run reconciliation and assert `state.json` logs `target_folder` as `01_Cat/Sub/Deep`.
     - Delete the physical shortcut, rerun reconciliation/regeneration, and assert it is regenerated correctly in the nested folder rather than the root category.
     - Assert the timeline view uses the correct `[Deep]` location tag.

## Verification
- Run `pytest` to ensure all tests pass.
- Start the application, manually move a generated shortcut into a new subfolder, reconcile, and verify `state.json` logs the nested path perfectly.
