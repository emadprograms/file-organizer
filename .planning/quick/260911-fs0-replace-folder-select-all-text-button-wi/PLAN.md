# Quick Task Plan: Replace Folder "Select All" Text Button with Checkbox that Reveals and Selects All Documents

**Task ID**: `260911-fs0`  
**Slug**: `replace-folder-select-all-text-button-wi`  
**Milestone**: v14.0 Power-User Operations & Portfolio Expansion (QCK-12)  
**Date**: 2026-09-11  

## Objective
Replace the verbose text button "Select All" / "Deselect All" on each folder card in the Categories/Folders view with a clean select checkbox (`.folder-select-checkbox`) placed right before the folder icon (matching the document row checkbox style). Clicking this checkbox reveals all documents in the folder (opening the folder if collapsed) and selects all documents, or unselects all if already selected.

## Requirements
1. **Folder Select Checkbox UI**:
   - In `categories-view.js`, remove the text button `selectAllFolderBtn` (`.btn-select-all-folder`).
   - Add a checkbox `.folder-select-checkbox` at the beginning of the folder card header, preceding `.folder-icon-box`:
     `<input type="checkbox" class="folder-select-checkbox w-3.5 h-3.5 rounded text-blue-600 focus:ring-blue-500 border-slate-300 cursor-pointer flex-shrink-0" ... />`
   - If the category has 0 documents, render a spacer `<span class="w-3.5 h-3.5 flex-shrink-0"></span>` to preserve visual alignment with folders having documents.
2. **Behavior on Click**:
   - Stop propagation so the card's collapse/expand toggle is not conflictingly triggered.
   - When clicked to select:
     - Reveals the documents container (`docsContainer.classList.remove('hidden')`).
     - Adds all document IDs in this folder to `selectedDocIds`.
     - Sets all child `.doc-select-checkbox` to checked.
     - Sets the folder checkbox to checked (`checked = true`, `indeterminate = false`).
     - Updates `updateBatchActionBar()`.
     - Updates global "Select All" / "Deselect All" button state if all documents are selected.
   - When clicked to unselect:
     - Removes all document IDs in this folder from `selectedDocIds`.
     - Sets all child `.doc-select-checkbox` to unchecked.
     - Sets the folder checkbox to unchecked.
     - Updates `updateBatchActionBar()`.
3. **Reactive State Syncing**:
   - When child document checkboxes are toggled, update parent `.folder-select-checkbox`:
     - 0 docs selected in folder: `checked = false`, `indeterminate = false`
     - All docs selected in folder: `checked = true`, `indeterminate = false`
     - Some docs selected in folder: `checked = false`, `indeterminate = true`
   - When global select all/deselect all runs, update all `.folder-select-checkbox` accordingly.
4. **Testing & Synchronization**:
   - Update `tests/frontend/components/batch_operations.test.js` to test the `.folder-select-checkbox`.
   - Add unit tests for revealing documents on click, selecting/deselecting, and indeterminate state.
   - Synchronize `src/api/static/js/categories-view.js` to `web-net/wwwroot/js/categories-view.js`.
   - Run Vitest and Playwright tests to ensure 100% pass rate.
