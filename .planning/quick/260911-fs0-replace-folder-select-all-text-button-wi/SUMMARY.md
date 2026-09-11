---
status: complete
quick_id: 260911-fs0
slug: replace-folder-select-all-text-button-wi
date: 2026-09-11
description: Replace Folder Select All Text Button with Checkbox that Reveals and Selects All Documents
commit: HEAD
---

# Quick Task Summary: Replace Folder "Select All" Text Button with Select Checkbox

**Task ID**: `260911-fs0`  
**Milestone**: v14.0 Power-User Operations & Portfolio Expansion (QCK-12)  
**Status**: Complete  
**Date**: 2026-09-11  

## Overview
Replaced the text-heavy "Select All" / "Deselect All" button on category folder cards with a streamlined select checkbox (`.folder-select-checkbox`) positioned right before the category folder icon (`.folder-icon-box`). Clicking this checkbox immediately opens/unfolds the category documents list (if collapsed) and selects all contained documents, or deselects all if already selected.

## Key Changes
1. **Category Folder Checkbox UI**:
   - Removed `.btn-select-all-folder` text button from folder cards in `categories-view.js`.
   - Placed a select checkbox (`.folder-select-checkbox`) before the folder icon with identical styling to document row checkboxes (`w-3.5 h-3.5 rounded text-blue-600 focus:ring-blue-500 border-slate-300 cursor-pointer flex-shrink-0`).
   - For categories with 0 documents, rendered an empty spacer (`<span class="w-3.5 h-3.5 flex-shrink-0"></span>`) to preserve consistent visual alignment across all category rows.
2. **Behavior on Checkbox Click**:
   - Clicking the folder checkbox stops event propagation to prevent conflicting card expansion toggles.
   - When selecting: removes the `hidden` class from the child documents container (`.category-docs`), revealing all documents, selects all documents in that folder into `selectedDocIds`, and checks all document checkboxes.
   - When deselecting: removes all documents in that folder from `selectedDocIds` and unchecks all document checkboxes.
   - Updates the floating batch action bar and synchronizes the global select all button.
3. **Reactive State Synchronization**:
   - Added `updateFolderCheckboxState(card, cat)` to compute folder checkbox state dynamically:
     - All documents selected: `checked = true`, `indeterminate = false`.
     - Some documents selected: `checked = false`, `indeterminate = true`.
     - No documents selected: `checked = false`, `indeterminate = false`.
   - Wired document row checkboxes (`.doc-select-checkbox`) on change to automatically update the parent folder's checkbox.
   - Synchronized global select all and deselect all actions to update all folder checkboxes across the view.
4. **Testing & Static Asset Synchronization**:
   - Updated `tests/frontend/components/batch_operations.test.js` to test folder select checkbox toggling, revealing documents, and partial selection indeterminate state.
   - Created dedicated test suite `tests/frontend/components/folder_select_checkbox.test.js` (8 tests) covering rendering, empty folder spacing, click reveal, select/deselect toggle, indeterminate state, and global sync.
   - Fully synchronized `src/api/static/js/categories-view.js` with `web-net/wwwroot/js/categories-view.js` (`diff -r` returns 0).
   - All 143 frontend Vitest tests across 13 files, 84 .NET xUnit tests, and 30 Python backend tests pass cleanly.
