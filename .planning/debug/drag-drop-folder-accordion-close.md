---
status: resolved
trigger: "when I move one document from one folder to another, all the open folder dialogues close. I get a beauitful successfully moved message at the bottom but the dialog closing very annoying. I am talking about the drag and drop feature. It still scrolls all the way to the top which kills immersion. for example, I moved a document from 10 to 11. It'll scroll all the way to 1."
created: 2026-09-12
updated: 2026-09-12
---

## Symptoms
- **Expected**:
  1. When dragging and dropping a document from one category folder to another (e.g., from folder 10 to folder 11), all open folder accordions should remain open, and the destination folder should expand.
  2. The scroll position within the categories list should be preserved so the viewport does not jump back to the top (folder 1).
- **Actual**:
  1. Upon dropping a document and receiving the success toast, all open folders collapsed closed.
  2. The categories container immediately scrolled all the way to the top (folder 1), breaking immersion when working on folders lower in the hierarchy.

## Root Causes
1. **Lack of Category Expansion State Tracking**:
   `categories-view.js` reconstructed all folder cards from scratch during `renderCategories()`, setting `.category-docs` classes unconditionally to `hidden` (unless the category had a noted document). Any cards the user clicked to expand were not recorded in state.
2. **Scroll Collapse from Loading Placeholder**:
   `loadCategories()` in `categories-view.js` unconditionally wiped `docListEl.innerHTML` with `'<p class="text-xs text-slate-500 p-3">Loading categories...</p>'` prior to fetching updated data. This temporary collapse of container height caused the browser to immediately reset `scrollTop = 0`.
3. **Missing Scroll Preservation & Target Focus**:
   When re-rendering completed cards, scroll offsets were neither saved nor restored, and no target focus logic existed to ensure the drop destination folder remained in view.

## Resolution
1. **Folder Expansion Persistence**:
   - Added `openCategoryNames = new Set()` in `categories-view.js`.
   - Before `docListEl.innerHTML` is cleared during `renderCategories()`, the existing DOM is scanned to retain open folders (within the same house/tenant scope).
   - Toggling a folder card via click or `toggleSelectAllInFolder` syncs with `openCategoryNames`.
   - Added `openCategoryFolder(categoryName)` helper and integrated it into `handleCategoryDrop`, `handleMoveDocSubmit`, `executeBatchMove`, and `handleBatchCopySubmit`.
2. **Scroll Offset Preservation & No-Flicker Reload**:
   - In `loadCategories()`, captured scroll offsets (`savedScrollOffsets`) and bypassed the temporary `'Loading categories...'` innerHTML wipe if category cards already exist.
   - Restored `scrollTop` after re-rendering cards.
   - Added `setPendingScrollCategory(catName)` and smooth `scrollIntoView({ block: 'nearest', behavior: 'smooth' })` targeting the drop destination so folders (e.g. 10 and 11) stay comfortably in view without jumping to folder 1.
   - Cleanly reset folder and scroll states when navigating to a different house or tenant (`isScopeChanged`).
3. **Multi-Stack Parity & Testing**:
   - Synchronized static assets across `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/`.
   - Created `tests/frontend/components/category_folder_persistence.test.js` with 8 comprehensive unit tests covering accordion persistence, drag-and-drop expansion, scroll position retention, and target folder scrolling.
   - All 195 Vitest tests across 22 test files passing.
