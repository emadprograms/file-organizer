---
status: resolved
trigger: "i changed the document date of the starting documents in house 616 but the house card still shows from1990. the tenant selection ui is okay. why does the house card and the tenant selection ui use separate logic."
created: 2026-09-14T09:37:00Z
updated: 2026-09-14T12:53:00Z
---

## Symptoms
- **Expected Behavior**: Changing the document date of the starting documents for a house (e.g. house 616) should update the house card tenure duration and start date in the Area Grid. The house card and the tenant selection UI (House Profile / Tenancy Register) should use unified logic and stay in sync.
- **Actual Behavior**: The house card still showed "from1990" (or outdated start year), whereas the tenant selection UI showed the updated date.
- **Error Messages**: None.
- **Timeline**: Observed after changing document dates.
- **Reproduction**: Change the document date of the starting document for a tenant/house, return to Area Grid; house card still showed previous start year while tenant selection UI showed the new date.

## Root Cause
The discrepancy between the house card and the tenant selection UI stemmed from multiple architectural disconnects across backend SQL queries, database state updates, and frontend tree refresh/navigation flows:

1. **Backend Query Discrepancy (Dynamic Date Derivation)**:
   - `GetHouseProfileAsync` and `GetTenantsAsync` dynamically derived each tenant's start date using:
     `CASE WHEN d.min_date IS NOT NULL AND d.min_date != '' THEN d.min_date ELSE t.start_date END`
     joined with `(SELECT tenant_id, MIN(primary_date) AS min_date FROM documents WHERE is_timeline_visible = 1 GROUP BY tenant_id) d`.
   - In contrast, `GetTreeAsync` (which populates the tree and Area Grid house cards) and `GetHousesAsync` queried `tenants` directly without joining `documents` on `MIN(primary_date)`. They read raw `t.start_date`. As a result, changing document dates had zero effect on `GetTreeAsync`.
   - `TreeTenantDto` did not expose `start_date` or `end_date`, and duration category calculations in `GetTreeAsync` and `GetHousesAsync` had slight discrepancies (`< 10` vs `<= 10`) and did not clamp negative durations to 0 (`Math.Max(duration, 0)`).

2. **Backend Mutation Desynchronization (`tenants.start_date` persistence)**:
   - When documents were updated (`UpdateDocumentAsync`), deleted (`DeleteDocumentAsync`), or batch deleted (`BatchDeleteDocumentsAsync`), the database column `tenants.start_date` was not synchronized with `MIN(primary_date)` of the remaining timeline-visible documents.

3. **Frontend Tree Refresh Disconnect**:
   - In `doc-manager.js`, `saveChangeDocDate`, `saveDocModal`, and `batchAssignTenant` only called `refreshCurrentTab()`, refreshing the house view but never triggering `window.loadTree()`.
   - When navigating back from the house view to the Area Grid (`router.js` and `app.js` `backToGridBtn`), `loadAreaGrid` was not invoked with fresh tree data, leaving the cards with stale in-memory state.

## Key Changes
1. **DTO Enhancement** (`src/HousingApplication.Web/Models/DTOs.cs`):
   - Added `start_date` and `end_date` properties to `TreeTenantDto`.

2. **Backend Repository Logic Unified** (`src/HousingApplication.Web/Data/FileOrganizerRepository.cs`):
   - `GetTreeAsync`: Updated tenant query to perform `LEFT JOIN (SELECT tenant_id, MIN(primary_date) AS min_date FROM documents WHERE is_timeline_visible = 1 GROUP BY tenant_id) d` and evaluate `effective_start_date = CASE WHEN d.min_date IS NOT NULL AND d.min_date != '' THEN d.min_date ELSE t.start_date END`.
   - Populated `StartDate` and `EndDate` on `TreeTenantDto`, and aligned duration calculation (`Math.Max(duration, 0)`, `<= 10` for medium tenure).
   - `GetHousesAsync`: Updated to use the same `LEFT JOIN` on `MIN(primary_date)` and aligned duration calculation.
   - `SearchAsync`: Updated tenant search query to use `effective_start_date` from `MIN(primary_date)`.
   - `UpdateDocumentAsync`: Added automatic recalculation and synchronization of `tenants.start_date` to `MIN(primary_date)` for affected tenant(s) (including old and new tenants when moving documents).
   - `DeleteDocumentAsync` & `BatchDeleteDocumentsAsync`: Added automatic recalculation and synchronization of `tenants.start_date` to remaining `MIN(primary_date)`.

3. **Frontend Tree & Grid Synchronization**:
   - `src/HousingApplication.Web/wwwroot/js/doc-manager.js` and `dist/win-x64/wwwroot/js/doc-manager.js`:
     - Added `if (typeof window.loadTree === 'function') { window.loadTree().catch(...); }` after document date changes in `saveChangeDocDate`, `saveDocModal`, and `batchAssignTenant`.
   - `src/HousingApplication.Web/wwwroot/js/router.js` and `dist/win-x64/wwwroot/js/router.js`:
     - In `handleHashChange()`, when navigating to an area view (`areaId && !houseId`), invoked `loadAreaGrid(areaId)`.
   - `src/HousingApplication.Web/wwwroot/js/app.js` and `dist/win-x64/wwwroot/js/app.js`:
     - In `backToGridBtn` click handler, invoked `loadAreaGrid(currentArea)`.

4. **Automated Unit Tests**:
   - `tests/HousingApplication.Tests/RepositoryTests.cs`:
     - `GetTreeAsync_And_GetHousesAsync_AccuratelyReflectDocumentAnchoredStartDate_WhenDocumentDateIsUpdated`: Verifies `GetTreeAsync` and `GetHousesAsync` dynamically reflect updated document dates as effective start date and adjust tenure durations/badges accordingly.
     - `DeleteDocumentAsync_UpdatesTreeAndHouseCardDocumentAnchoredStartDate`: Verifies deleting earliest document recalculates start date to next earliest document.
   - `tests/web/components/doc_dropdown_and_date.test.js`:
     - Added test verifying `window.loadTree()` is called upon saving document date changes.
   - `tests/web/components/area_grid_card.test.js`:
     - Added tests verifying house card tenure duration subtitle (`From YYYY`) and badge (`< 5 Yrs`, `> 10 Yrs`) react dynamically to document date changes, and `loadAreaGrid` refreshes the UI.

## Verification
- Ran C# unit tests: `~/.dotnet/dotnet test` -> Passed 184/184 tests (0 failures, 0 warnings).
- Ran Frontend JS unit tests: `npm test` -> Passed 31/31 test files, 358/358 tests (0 failures).
- All changes replicated to both `src/HousingApplication.Web/wwwroot` and `dist/win-x64/wwwroot`.
