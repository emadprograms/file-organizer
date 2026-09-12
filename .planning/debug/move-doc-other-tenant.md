---
status: resolved
trigger: "when I move the document to another tenant in the same house. the document doesn't moves but it still keeps showing until I click refresh. take a look at this. it works fine and disappears if I move into the same tenant but when I multiselect or single select and move to another tenant in the same house. it doesn't disappear. make tests. fix this. update the milestone. commit and push changes."
created: 2026-09-12
updated: 2026-09-12
---

## Symptoms
- **Expected**:
  - When moving document(s) (via single select / 3-dots Move Document, multi-select Batch Move modal, or tree drag-and-drop) to another tenant in the same house, the document(s) should immediately be removed from the current tenant's category folder view without requiring a manual page refresh.
- **Actual**:
  - Moving within the same tenant moved the document element from source folder to target folder in the DOM. However, when moving to another tenant in the same house, the document stayed visible in the current tenant's folder list until the user clicked refresh.
- **Reproduction**:
  - Drill down into a tenant's category folders.
  - Select one document (via 3-dots -> Move Document) or multiple documents (via multi-select -> Move Selected).
  - Select a different tenant from the `#batch-move-tenant-select` dropdown in the modal (within the same house), and confirm the move.
  - Observe that the document remained visible in the current tenant's view until a page/tab refresh was clicked.

## Root Causes
1. **False Assumption in DOM Move Routing**:
   - In `categories-view.js:handleBatchMoveSubmit`, when moving documents, the handler unconditionally invoked `moveDocInDom(id, null, targetFolder)`.
   - `moveDocInDom` assumed the target folder was located within the *currently displayed* tenant's view. If the target category folder matched the source category folder (`sourceCard === targetCard`), `moveDocInDom` did not remove the document at all and returned `true`. If the target folder was different, it appended the document element to that folder within the current tenant's view.
   - Because `moveDocInDom` returned `true`, `allMovedInDom` was evaluated as `true`, preventing `window.refreshCurrentTab` from running automatically. Consequently, the document remained visible in the current tenant's view until manual refresh.
2. **Missing Instant DOM Removal Helper**:
   - The frontend lacked a dedicated `removeDocFromDom(vaultId, sourceCatName)` utility to handle cross-tenant relocations by removing the document element, decrementing the source folder count badge, removing empty folder cards, showing the empty state when no folders remain, and updating overall category statistics.

## Resolution
1. **Cross-Tenant Move Detection (`isMovingToOtherTenant`)**:
   - In `categories-view.js`, captured `select.dataset.sourceTenantId` and `sourceTenantName` during `renderTenantOptions` and reset them in `openBatchMoveModal`.
   - Implemented `isMovingToOtherTenant(targetTenantVal, targetVaultIds, targetDoc)` which checks whether `targetTenantVal` differs from the source tenant ID, `singleTargetDoc.tenant_id`, the active view tenant, or documents in `currentCategories`.
2. **Instant Cross-Tenant Removal (`removeDocFromDom`)**:
   - Implemented `removeDocFromDom(vaultId, sourceCatName)`:
     - Removes `docEl` from the DOM immediately.
     - Decrements the source folder card's count badge.
     - If the folder count reaches 0, removes the folder card from DOM, clears open folder tracking, and if all cards are gone, renders the empty state message (`No folders found for this selection.`).
     - Updates in-memory `currentCategories` and category statistics (`stats-badge`).
     - Removes document card from DOM and updates `currentTimeline` if in Timeline view.
   - Exposed `removeDocFromDom` and `isMovingToOtherTenant` on `window` and `module.exports`.
3. **Wired Clean Cross-Tenant Handlers**:
   - In `handleBatchMoveSubmit`: If `isToOtherTenant` is `true`, invokes `removeDocFromDom(id)` for each moved document and triggers `await window.refreshCurrentTab(activeArea, activeHouse)` to synchronize backend state. If `isToOtherTenant` is `false`, preserves `moveDocInDom` for same-tenant moves.
   - In `doc-manager.js:executeDocModalSubmit`: If `newTenantId` is different from the document's `tenant_id`, invokes `removeDocFromDom` followed by `refreshCurrentTab`.
   - In `doc-manager.js:handleTenantTreeDrop`: When dragging and dropping onto another tenant in the sidebar tree, invokes `removeDocFromDom` for each dropped document before triggering `refreshCurrentTab`.
4. **Synchronized Multi-Stack Assets**:
   - Kept zero diff across `src/api/static/js/`, `web-net/wwwroot/js/`, and `dist/win-x64/wwwroot/js/` for both `categories-view.js` and `doc-manager.js`.
5. **Comprehensive Automated Testing**:
   - Created `tests/frontend/components/move_to_other_tenant.test.js` covering tenant change detection, `removeDocFromDom`, folder disappearance on empty, empty state message, single document move to other tenant, multi-select move to other tenant, and same-tenant moves.
   - All 27 Vitest frontend test files and 273 tests passing (`npm run test:frontend`). All 18 Python backend tests passing (`test_v14_features.py`).
