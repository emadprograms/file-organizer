---
status: resolved
trigger: "house 504. the house card says that number 7 document is missing but the integration test inside the tenant selection says that it is okay. the document is present. I moved the document from another tenant's file."
created: 2026-09-17
updated: 2026-09-17
---

## Symptoms
- **Expected behavior**: In Area Grid, House 504's card should reflect the presence of document #7 ("07 - استقطاع إيجار" / Rent Deduction) for the active resident tenant and display the complete badge `5/5` without a missing document warning.
- **Actual behavior**: House 504 card showed `⚠️ ناقص: استقطاع إيجار 4/5` on the Area Grid, even though Tenant Selection / House Profile (`house-profile.js`) showed the tenant compliance as `5/5` and all 5 mandatory documents present.
- **Trigger**: The document had been moved from another tenant's file to the active resident tenant (`أحمد يوسف المريسل`).

## Root Cause
1. **Frontend State Staleness**:
   - Inside Tenant Selection / House Profile, navigating to the house triggers `loadHouseProfile`, fetching `/api/areas/{areaId}/houses/{houseId}` directly from SQLite where the move was recorded.
   - On the Area Grid, cards render from `window.globalTreeData`.
   - When documents were moved (`handleBatchMoveSubmit` in `categories-view.js` and `doc-manager.js`), `window.loadTree()` was not called.
   - When returning to the grid via `backToGridBtn` (`app.js`), the stale in-memory `globalTreeData` was rendered without re-fetching `/api/tree`.
2. **Backend Category Count Matching**:
   - When building category count dictionaries in `FileOrganizerRepository.cs` (`GetTreeAsync`, `GetHousesAsync`, `GetHouseProfileAsync`), keys were only indexed by cleaned names, omitting the raw category string (e.g. `'07 - استقطاع إيجار'`) which could prevent exact prefix matches.
3. **Frontend Category Matching Parity**:
   - `computeHouseIntegrity` in `area-grid.js` was updated to support both clean name (`cleanK === cat.key`) and ID / prefix matching (`k.includes(cat.prefix) || k.startsWith(cat.id)`), mirroring the resolution logic in `house-profile.js`.

## Solution & Verification
- Updated `categories-view.js` (`handleBatchMoveSubmit`, `handleBatchCopySubmit`, `handleBatchDeleteSubmit`), `doc-manager.js` (drag-and-drop moves), and `tenant-manager.js` to call `await window.loadTree()` upon document mutations.
- Updated `backToGridBtn` in `app.js` to await `window.loadTree()` before navigating back to the area grid.
- Updated `FileOrganizerRepository.cs` to index both clean and raw category formats in `active_tenant_category_counts`.
- Maintained 100% dual-asset parity between `src/HousingApplication.Web/wwwroot/` and `dist/win-x64/wwwroot/`.
- Added unit tests in `tests/HousingApplication.Tests/RepositoryTests.cs` (all 956 .NET tests passing).
- Added unit tests in `tests/web/components/area_grid_card.test.js` and `tests/web/components/move_to_other_tenant.test.js` (all 514 Vitest tests passing).
