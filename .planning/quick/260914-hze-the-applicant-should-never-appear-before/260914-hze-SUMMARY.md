---
status: complete
task_id: 260914-hze
slug: the-applicant-should-never-appear-before
date: 2026-09-14
---

# Quick Task Summary: Ensure Applicants Never Appear Before Resident Tenants

**Task ID**: `260914-hze`  
**Status**: Complete  
**Date**: 2026-09-14  

---

## 1. Overview
Addressed user feedback: *"the applicant should never appear before the tenant. fix this as well. update the tests. commit and push"*.

Prior to this fix, applicants (`is_resident === 0` / `is_resident === false`) could sort before or interleave with resident tenants in several areas:
1. **Area Grid House Cards (`area-grid.js`)**: `allTenants` was mapped directly without guaranteeing resident tenants preceded applicants in DOM rendering.
2. **Backend Tree Queries (`FileOrganizerRepository.cs`)**: `GetTreeAsync` and `GetTreeAreaAsync` omitted `t.is_resident DESC` from their `ORDER BY` clause. Because applicants often have a NULL end date and newer application/start date, the active tenancy SQL CASE statement ranked applicants alongside or ahead of past/current residents.
3. **House Profile & Global Search (`FileOrganizerRepository.cs`)**: `GetHouseProfileAsync` in-memory sorting checked `IsActive` before `IsResident`, allowing active applicants to be sorted alongside residents. `SearchGlobalAsync` did not prioritize residents on score ties.
4. **Tenant Selection Dropdowns and Modals**: `categories-view.js`, `ingest-station.js`, `tenant-manager.js`, and `command-palette.js` needed explicit residency sorting guarantees so applicants always follow resident tenants.

---

## 2. Changes Made
1. **Backend Database Repository (`src/HousingApplication.Web/Data/FileOrganizerRepository.cs`)**:
   - `GetTreeAsync`: Added `t.is_resident DESC` as the primary sort key in the tenant query.
   - `GetTreeAreaAsync`: Added `t.is_resident DESC` as the primary sort key in the tenant query.
   - `GetHouseProfileAsync`: Updated `tenantProfiles.Sort(...)` so `b.IsResident.CompareTo(a.IsResident)` is evaluated first before `IsActive`, `EndDate`, and `StartDate`.
   - `SearchGlobalAsync`: Added `.ThenByDescending(x => x.Dto.IsResident)` to ensure resident tenants appear before applicants when relevance scores are tied.

2. **Frontend Area Grid (`area-grid.js`)**:
   - Partitioned and re-composed tenants into `orderedTenants = [...residents, ...applicants]`.
   - Mapped `orderedTenants` in DOM card rendering and used `orderedTenants.length > 3` for the scrollable container check.
   - Maintained 1:1 byte parity with `dist/win-x64/wwwroot/js/area-grid.js`.

3. **Frontend Dropdowns, Dialogs, and Search**:
   - `categories-view.js`: Sorted `sortedTenantsList` by residency before rendering `<option>` elements in `renderTenantOptions`.
   - `ingest-station.js`: Sorted fetched tenants from API and fallback tree children by residency descending so resident tenants always appear before applicants in the ingestion select box.
   - `tenant-manager.js`: Sorted modal rows in the "Manage Tenants" dialog so resident tenants appear at the top.
   - `command-palette.js`: Sorted tenant search results by residency descending so resident tenants appear before applicants.
   - `house-profile.js`: Ensured static fallback mode sorts residents before applicants.
   - Maintained 100% byte-for-byte parity across `src/HousingApplication.Web/wwwroot/js/` and `dist/win-x64/wwwroot/js/`.

4. **Automated Unit & Integration Tests**:
   - `tests/web/components/area_grid_card.test.js`: Added test verifying that when `house.children` lists applicants before resident tenants, the rendered DOM orders all resident tenants before any applicant.
   - `tests/web/components/command_palette_tenants.test.js`: Added test verifying search results display resident tenants ahead of applicants.
   - `tests/HousingApplication.Tests/RepositoryTests.cs`: Added `Applicants_NeverAppearBeforeResidentTenants_InTree_And_HouseProfile` asserting that `GetTreeAsync`, `GetHousesAsync`, `GetHouseProfileAsync`, and `GetTenantsAsync` all return residents before applicants even if an applicant was inserted into the database first and has a later date with NULL end date.

---

## 3. Verification Results
- **.NET Unit Tests**: 185 / 185 tests passed (`~/.dotnet/dotnet test`).
- **Vitest Unit Tests**: 31 / 31 test files passed, 360 / 360 tests passed (`npm test`).
- **Asset Parity**: Exact 1:1 diff verification between `src/HousingApplication.Web/wwwroot/` and `dist/win-x64/wwwroot/`.
