---
status: resolved
trigger: "when I move one document from one folder to another, all the open folder dialogues close. I get a beauitful successfully moved message at the bottom but the dialog closing very annoying. I am talking about the drag and drop feature. It still scrolls all the way to the top which kills immersion. for example, I moved a document from 10 to 11. It'll scroll all the way to 1."
created: 2026-09-12
updated: 2026-09-12
---

## Symptoms
- **Expected**:
  1. When moving or copying a document (via drag & drop, 3-dots action menu, or batch operations), **absolutely nothing in the UI hierarchy or scroll position should change**.
  2. Nothing that is open should close, and nothing that is closed should open (the target folder must not be forced open).
  3. Scroll position must remain rock-solid with zero jump or displacement (no `scrollIntoView` shifting).
  4. Only the document itself should move or copy in the DOM and in-memory state, count badges should update accurately, and the bottom toast notification should be displayed.
- **Actual (Earlier Iterations)**:
  1. In the original version, all folders collapsed and scroll jumped to folder 1 due to full DOM wipe and lack of state persistence.
  2. In the intermediate fix, the target folder was forced open via `openCategoryFolder(targetCategory)` and `scrollIntoView` jumped the viewport to the target folder, breaking immersion when working on other folders.

## Root Causes
1. **Unnecessary DOM Reconstruction & State Shifting**:
   Re-running full tab renders (`refreshCurrentTab` / `loadCategories`) triggered height changes and re-evaluated open/closed states.
2. **Forced Target Accordion Expansion**:
   Code explicitly called `openCategoryFolder(finalCategory)` on move and copy operations, forcing closed folders to expand.
3. **Viewport Displacement via `scrollIntoView`**:
   Code called `targetCard.scrollIntoView(...)` or `setPendingScrollCategory(catName)`, which animated or snapped the viewport to the target category.
4. **`sourceCategory` Undeclared Variable**:
   In `doc-manager.js:handleCategoryDrop`, `sourceCategory` was referenced without declaration prior to `moveDocInDom`, causing a ReferenceError inside the `try` block.
5. **Scope State Timing in `renderCategories`**:
   `lastRenderedScope = currentScope` was assigned before checking `lastRenderedScope === null`, preventing initial note folder auto-expansion in test harnesses.

## Resolution
1. **In-Place DOM & In-Memory Operations (`moveDocInDom` & `copyDocInDom`)**:
   - Implemented `moveDocInDom(vaultId, sourceCatName, targetCatName)`: Moves the existing DOM element directly into the target card's `.category-docs` container, updates data attributes, drag event handlers, and badge counts without touching any folder's open/closed state or scrolling.
   - Implemented `copyDocInDom(newDoc, targetCatName)`: Constructs a new document element via `createDocRowElement` and appends it to target `.category-docs` container, updating counts and stats badge with zero layout disruption.
2. **Complete Accordion Immutability**:
   - Removed all calls to `openCategoryFolder(...)` from drag-and-drop drop handlers, 3-dots modal submit handlers, and batch operations.
   - If the destination folder is closed (`hidden`), it remains closed. If open, the new document row appears immediately inside it.
   - Open folders remain open; closed folders remain closed.
3. **Zero Scroll Displacement**:
   - Completely eliminated all calls to `scrollIntoView(...)` and `setPendingScrollCategory(...)` across `categories-view.js` and `doc-manager.js`.
   - Scroll offsets (`scrollTop`) are fully locked and preserved across any background data synchronizations.
4. **Scope Timing & Variable Fixes**:
   - Explicitly defined `const sourceCategory = activeDragged.category;` in `doc-manager.js:handleCategoryDrop`.
   - Refactored `renderCategories()` to evaluate `const isInitialLoad = lastRenderedScope === null;` and `const isScopeChanged = !isInitialLoad && lastRenderedScope !== currentScope;` before assigning `lastRenderedScope = currentScope;`.
   - Handled `global.refreshCurrentTab` compatibility in batch copy while maintaining complete scroll and accordion preservation.
5. **Multi-Stack Asset Synchronization**:
   - Kept exact zero-diff byte parity across `src/api/static/js/`, `web-net/wwwroot/js/`, and `dist/win-x64/wwwroot/js/`.
6. **Comprehensive Automated Testing**:
   - Created 10 automated unit tests in `tests/frontend/components/category_folder_persistence.test.js`:
     1. Initial render collapses folders without notes.
     2. Clicking a folder expands it, and re-rendering preserves the expanded state.
     3. Preserves multiple open folders across re-renders.
     4. Preserves closed folders after other folders are opened.
     5. Resets open folders when switching to a different house.
     6. Drag and drop move preserves open folders without opening closed target folders and preserves scroll.
     7. Preserves scroll position across re-renders within the same house.
     8. Does not jump or scroll when moving documents (`scrollIntoView` not called).
     9. Copying a document preserves open/closed folder states and updates count without scroll jump.
     10. `executeBatchMove` moves docs in DOM and preserves open/closed folders without scrolling.
   - All 197 Vitest tests across 22 test files passing (100%).
