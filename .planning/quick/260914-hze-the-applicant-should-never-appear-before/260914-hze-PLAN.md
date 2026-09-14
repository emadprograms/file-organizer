# Quick Task 260914-hze: Ensure applicants never appear before resident tenants anywhere in the application

## Overview
The user requested: "the applicant should never appear before the tenant. fix this as well. update the tests. commit and push".
Currently, applicants (`is_resident === 0` / `is_resident === false`) could appear before resident tenants (`is_resident !== 0`) in several places:
1. **Area Grid House Cards (`area-grid.js`)**: `house.children` elements of type `tenant` are rendered in raw order rather than prioritizing residents before applicants.
2. **Backend Tree Queries (`FileOrganizerRepository.cs`)**: `GetTreeAsync` and `GetTreeAreaAsync` omit `t.is_resident DESC` from their `ORDER BY` clause, causing applicants without an end date to be sorted as active alongside or ahead of resident tenants.
3. **Backend House Profile & Global Search (`FileOrganizerRepository.cs`)**: `GetHouseProfileAsync` in-memory sorting sorts by `IsActive` before `IsResident`, and `SearchGlobalAsync` does not prioritize resident tenants on tied scores.
4. **Dropdown Selects & Modals (`categories-view.js`, `ingest-station.js`, `tenant-manager.js`, `command-palette.js`)**: Tenant selection dropdowns and search modals must consistently place resident tenants before applicants.

## Tasks
1. **Backend Database Repository (`FileOrganizerRepository.cs`)**:
   - In `GetTreeAsync` and `GetTreeAreaAsync`: add `t.is_resident DESC` as the primary tenant sort key in the SQL query.
   - In `GetHouseProfileAsync`: update `tenantProfiles.Sort(...)` so `b.IsResident.CompareTo(a.IsResident)` is checked first before `IsActive` and dates.
   - In `SearchGlobalAsync`: order scored tenant results by score descending, then `IsResident` descending.
2. **Frontend Area Grid (`area-grid.js`)**:
   - Order tenants as `[...residents, ...applicants]` before mapping HTML elements and checking scroll height.
   - Mirror changes to `dist/win-x64/wwwroot/js/area-grid.js`.
3. **Frontend Dropdowns & Dialogs (`categories-view.js`, `ingest-station.js`, `tenant-manager.js`, `command-palette.js`)**:
   - `categories-view.js`: sort tenant list in `renderTenantOptions` so residents precede applicants.
   - `ingest-station.js`: sort API-fetched tenants and fallback tree children so residents precede applicants.
   - `tenant-manager.js`: sort tenants in the Manage Tenants dialog so residents appear first.
   - `command-palette.js`: sort tenant search results so residents appear before applicants.
   - Mirror all changed JS files to `dist/win-x64/wwwroot/js/`.
4. **Automated Testing & Verification**:
   - Update/add Vitest tests in `tests/web/components/area_grid_card.test.js` to assert that when `house.children` has an applicant before a resident, the resident renders first in the DOM.
   - Add a unit test in `tests/HousingApplication.Tests/RepositoryTests.cs` verifying `GetTreeAsync`, `GetTreeAreaAsync`, and `GetHouseProfileAsync` return residents before applicants regardless of start or end dates.
   - Run full test suites (`npm test` and `dotnet test`).
