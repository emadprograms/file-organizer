---
status: resolved
trigger: "why don't I get the pinned or lock symbol when I move the documents around manually now. why has the code regressed?"
created: 2026-09-14
updated: 2026-09-14
slug: manual-move-pinned-lock
---

## Symptoms
- **Expected**: Moving documents around manually (via drag & drop, touch drag, batch move modal, or Document Management modal) should immediately show the pinned/lock symbol (`🔒`) on the moved document, and update in-memory state so the document is marked `is_manual: 1` (protected from auto-reallocation).
- **Actual**: When moving documents manually, the document moved into the target folder without showing the pinned or lock symbol (`🔒`). The 3-dot dropdown menu continued to show "Pin Document" instead of "Unpin Document", and filtering by tenant still rendered it without the lock symbol.
- **Errors**: None (silent visual and in-memory state omission).
- **Timeline**: Worked originally when moving documents called `refreshCurrentTab(area, house)`, which queried SQLite where `is_manual` was set to 1. Regressed when `moveDocInDom` was introduced for zero-motion drag-and-drop to prevent viewport scrolling and accordion collapse.
- **Reproduction**:
  1. Open a house in Categories View.
  2. Drag and drop any auto-assigned document (which lacks `🔒`) to a different category folder.
  3. The document moves to the new folder, but lacks the `🔒` symbol.

## Root Causes
1. **Optimistic In-Place Relocation Without State Transition**:
   - In commit `8f80e40` (and session `drag-drop-folder-accordion-close`), all document move paths (single drag-and-drop, multi-select drag-and-drop, batch move modal, touch drag-and-drop, and Document Management modal) were converted to call `moveDocInDom(vaultId, sourceCatName, targetCatName)` to eliminate full page reloads (`refreshCurrentTab`) that caused viewport displacement and accordion collapses.
   - While `moveDocInDom` moved the physical `docEl` element in the DOM (`targetDocsContainer.appendChild(docEl)`), it **failed to transition the document's manual lock state**:
     - `docObj.is_manual` was never set to `1` on `docEl._docData`.
     - `movedDoc.is_manual` was never set to `1` in the `currentCategories` in-memory collection.
     - The lock badge/symbol (`🔒`) was never injected into `docEl`.
     - In the branch where a target category folder was newly created (`!targetCard`), `docData.is_manual` was omitted, so dynamically generated cards also lacked the lock symbol.
2. **Delayed Synchronization Until Full Page Reload**:
   - The backend API (`PATCH /documents/{id}` and `POST /documents/batch-move`) was properly persisting `is_manual = 1` in SQLite (`UPDATE documents SET category = @Category, is_manual = 1 WHERE vault_id = @VaultId`).
   - However, because the frontend was avoiding a full reload, the client stayed desynchronized until a manual browser refresh (Cmd+R).

## Resolution
1. **Updated `moveDocInDom` in `src/HousingApplication.Web/wwwroot/js/categories-view.js`**:
   - Set `docObj.is_manual = 1` and `docEl._docData.is_manual = 1` immediately on relocation.
   - Set `movedDoc.is_manual = 1` and `docData.is_manual = 1` in the `currentCategories` array so subsequent filterings or in-memory re-renders preserve the manual lock.
   - Dynamically injected the `🔒` lock element (`span.doc-lock-icon[title="Manually assigned - protected from auto-reallocation"]`) adjacent to `.doc-title-text` if not already present.
   - Ensured dynamically created target category cards (`!targetCard`) initialize `docData.is_manual = 1` so `createCategoryCardElement` renders the lock icon directly.
2. **Standardized Class Names**:
   - Added class `doc-lock-icon` to the `<span>🔒</span>` generated in `createDocRowElement` for consistent querying and styling across renders.
3. **Multi-Stack Synchronization**:
   - Synchronized `src/HousingApplication.Web/wwwroot/js/categories-view.js` with `dist/win-x64/wwwroot/js/categories-view.js`.
4. **Automated Verification**:
   - Added 2 new tests to `tests/web/components/category_folder_persistence.test.js`:
     - Verified `moveDocInDom` sets `is_manual: 1` and injects `🔒` into `docEl` in existing folders.
     - Verified `moveDocInDom` into a newly created folder renders the lock icon and sets `is_manual: 1`.
   - Added assertions to `tests/web/components/multi_select_drag_and_drop.test.js` confirming all multi-selected dragged documents receive `🔒` upon dropping.
   - All 350 Vitest tests passing across 31 test suites.
