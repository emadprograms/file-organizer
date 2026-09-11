# Quick Task Summary: Document 3-Dots Dropdown Action Menu & Folders Section Document Date Badge (QCK-08)

**Task ID**: `260911-doc-menu-dropdown-and-folder-date`  
**Milestone**: v14.0 Power-User Operations & Portfolio Expansion (QCK-08)  
**Status**: Completed  
**Date**: 2026-09-11  

---

## 1. Executive Summary
Replaced the oversized, redundant Document Action Modal (`#doc-action-modal`) when clicking the 3-dots button (`.doc-menu-btn`) with an ergonomic, floating dropdown action menu providing single-click access to:
1. **Rename Document**: Focuses and triggers inline title editing on the document element (`handleInlineRename` / `handleInlineRenameTimeline`).
2. **Move Document**: Pre-selects the document and opens the category Move modal (`openBatchMoveForDoc`).
3. **Copy Document**: Pre-selects the document and opens the category Copy modal (`openBatchCopyForDoc`).
4. **Show in Timeline**: Switches the active view tab to the Timeline, resets any conflicting tenant filters, smoothly scrolls the timeline card into center viewport, highlights it with an active pulse (`ring-4 ring-blue-500 bg-blue-50`), and sets it as the selected document.
5. **Delete Document**: Prompts for confirmation and invokes `DELETE /api/areas/{area}/houses/{house}/documents/{vault_id}` with full cache and tab refreshing.

In addition, in the Folders / Categories section (`categories-view.js`), added an always-visible document date badge with a light gray background (`doc-date-badge bg-slate-100 text-slate-500 text-[10px] font-mono`) immediately preceding the 3-dots button so users can immediately distinguish document chronology within folders.

---

## 2. Changes Implemented

### Frontend (`src/api/static/js/` & `web-net/wwwroot/js/`)
- **`doc-manager.js`**:
  - `openDocDropdownMenu(e, doc, currentCategory, triggerBtn)`: Builds and attaches a floating dropdown menu anchored to the 3-dots button with auto-placement, bounds detection, Escape key dismissal, and outside-click dismissal.
  - `closeDocDropdownMenu()`: Global teardown function that cleans up DOM elements and event listeners.
  - `showDocInTimeline(doc)`: Handles seamless cross-tab navigation from folders to timeline view with smooth center scrolling and temporary pulse highlighting.
  - `handleDeleteSingleDoc(doc)`: Executes individual document deletion with confirmation dialog, API deletion call, and UI updates.
  - Exported all new functions to `window` and `module.exports`.
- **`categories-view.js`**:
  - Added `openBatchMoveForDoc(doc)` and `openBatchCopyForDoc(doc)` helpers and exported them.
  - Updated document row markup in `renderCategories` to render `<span class="doc-date-badge text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200/70 flex-shrink-0 select-none">${escapeHtml(docDate)}</span>` before `.doc-menu-btn`.
  - Replaced legacy `openDocModal` call in `menuBtn.onclick` with `openDocDropdownMenu(e, doc, cat.name, menuBtn)`.
- **`timeline-view.js`**:
  - Replaced legacy `openDocModal` call in `menuBtn.onclick` with `openDocDropdownMenu(e, doc, doc.category, menuBtn)`.

### Test Automation & Verification
- **`tests/frontend/components/doc_dropdown_and_date.test.js`**:
  - 13 comprehensive unit tests validating dropdown rendering, all 5 actions, dismissal behaviors (Escape, click-outside, toggle), date badge rendering, and timeline navigation.
- **Full Test Suite Results**:
  - Vitest: 11 test files, 126 passed (0 failures).
  - .NET xUnit: 84 passed (0 failures).
  - Python pytest: 30 passed (0 failures).
  - Static asset parity: 100% diff-clean between `src/api/static/js/` and `web-net/wwwroot/js/`.
