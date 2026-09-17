---
status: resolved
trigger: "changing the date of the document in the tenant timeline resets the page and moves me to the categories folder. the page should remain as is. just the document should re-adjust itself."
created: 2026-09-17
updated: 2026-09-17
---

## Current Focus
- status: resolved
- resolution: "Prevented loadTree from being called during saveChangeDocDate, prevented handleHashChange from resetting currentTab when area/house/tenant context has not changed, added reorderTimelineCard for instant in-place chronological re-sorting in timeline view, and made loadTimeline silent when documents are already loaded to preserve scroll position."

## Symptoms
1. **Expected behavior**: In the tenant timeline view, when changing a document's date via the 3-dots "Change Date" modal, the page stays on the timeline view, does not reset or reload the page, and the document card immediately re-adjusts its chronological position within the timeline list.
2. **Actual behavior**: Changing the date wiped the document list, reset the page, and jumped the user to the Categories folder.
3. **Error messages**: None (state/navigation reset bug).
4. **Timeline**: Resolved in this session.
5. **Reproduction**: Navigate to a tenant timeline (`#/area/.../house/.../tenant/...` with Timeline tab selected). Click 3 dots on a document -> Change Date -> enter new date -> Save Date. The page previously flashed and switched to Categories view.

## Root Cause
1. `saveChangeDocDate` in `doc-manager.js` called `await window.loadTree()` after saving. A document date update does not change areas or houses in the sidebar tree.
2. `loadTree` in `sidebar.js` calls `window.handleHashChange()` upon completion.
3. `handleHashChange` in `router.js` unconditionally reset `currentTab = 'categories'` whenever `tenantName` was in the hash, without checking if the user was already in that exact tenant context (`isDifferentContext`).
4. `selectHouse` then ran `refreshCurrentTab`, which saw `currentTab === 'categories'` and called `loadCategories()`, transporting the user from the timeline to the categories folder.
5. `loadTimeline` in `timeline-view.js` wiped `#document-list` with `Loading documents...` even when cards were already present, resetting scroll position to 0 and causing a visual flash.
6. Timeline cards lacked `data-date` attributes and did not have an in-place re-ordering method to dynamically adjust their chronological order in the DOM without a full page reload.

## Key Changes
1. **Frontend Controller (`router.js`)**:
   - In `handleHashChange()`, added `isDifferentContext` check (`areaId !== currentArea || houseId !== currentHouse || tenantName !== currentTenant`).
   - Only defaults `currentTab = 'categories'` when entering a *different* context, preserving `currentTab = 'timeline'` during in-context updates and re-renders.
2. **Document Manager (`doc-manager.js`)**:
   - In `saveChangeDocDate()`, removed `loadTree()` invocation.
   - Added immediate in-place timeline re-adjustment by calling `reorderTimelineCard(activeDateModalDoc.vault_id, newDate)` when `currentTab === 'timeline'`.
3. **Timeline View (`timeline-view.js`)**:
   - Added `data-date` attribute to timeline cards during `renderTimeline()`.
   - Implemented `reorderTimelineCard(vaultId, newDate)`: updates the card's date label, updates `data-date`, re-sorts in-memory collections, and repositions the DOM card in chronological descending order relative to its sibling cards with a brief smooth highlight.
   - Updated `loadTimeline` to silently fetch and update when cards are already rendered, restoring `docListEl.scrollTop` to prevent scroll jumps and eliminate the loading flash.
4. **Testing & Verification**:
   - Updated `tests/web/components/doc_dropdown_and_date.test.js` to assert `loadTree` is not called.
   - Created `tests/web/components/timeline_date_change.test.js` verifying chronological DOM re-ordering, tab preservation on date change, context stability in `handleHashChange`, and silent scroll-preserved updates in `loadTimeline`.
   - All 39 test files (510 tests) passing with zero failures.
