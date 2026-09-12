---
status: complete
date: 2026-09-12
task_id: 260912-jf8
---

# Quick Task 260912-jf8: Vacant House Grey Styling and Remove False Active Tenant Fallback

## Overview
When a house has no active tenant (all past tenants vacated in prior years, e.g. house 538 vacated in 2024), the backend previously fell back to `activeTenant = hTenants[0]` and forced tenure duration calculation as if the past tenant were still residing. This erroneously assigned `ActiveResident` / `CurrentTenant` and calculated `DurationCategory = "long"` (red border and `> 10 Yrs` badge) based on their start date. In addition, the frontend had a fallback `(idx === 0 && !t.subtitle?.includes('-'))` that highlighted the first past tenant with colored backgrounds/icons if their subtitle was a single year (e.g. `2024`), and rendered the tenure badge with `Unknown` when duration category was null.

## Changes Made
- **Backend .NET (`web-net/Data/FileOrganizerRepository.cs`)**:
  - `GetTreeAsync`: Removed fallback `if (activeTenant == null && hTenants.Count > 0) activeTenant = hTenants[0];`. When no active tenant exists, `activeTenant`, `CurrentTenant`, and `DurationCategory` stay `null`. Tenant nodes have `isActive = false`, `DurationCategory = null`, and subtitle without "Present".
  - `GetHouseCardsAsync`: Removed fallback `if (activeTenant == null && hTenants.Count > 0) activeTenant = hTenants[0];`. When vacant, `ActiveTenant` and `DurationCategory` remain `null`, and `TenureColor = "grey"`.
  - `GetHouseProfileAsync`: Line 495 updated to `ActiveResident = activeTenant?.Name,` (no longer falls back to `tenantProfiles.FirstOrDefault()?.Name`).
  - Added unit test `GetHousesAsync_And_GetTreeAsync_VacantHouse_ReturnsGreyAndNoActiveTenant` in `web-net/FileOrganizer.Tests/RepositoryTests.cs`.
- **Backend Python (`src/api/routes.py`, `src/presentation/export_static.py`, `scripts/export_web.cjs`)**:
  - `src/api/routes.py`: Removed fallback `if not active_t and h_tenants: active_t = h_tenants[0]`. Required `cand` in `house_id` to be active. Filesystem tree only sets `active_tenant` if `tenant_is_present` is true.
  - `src/presentation/export_static.py` & `scripts/export_web.cjs`: Required `tenant_is_present` before assigning `active_tenant`.
  - Added unit test `test_get_tree_vacant_house_no_active_tenant` in `tests/test_api_v11.py`.
- **Frontend Core Logic (`src/api/static/js/area-grid.js`)**:
  - Default card border changed to `border-l-[5px] border-l-slate-300 dark:border-l-slate-600 hover:border-slate-400`.
  - Default tenure badge changed to `bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700 font-medium` with `badgeLabel = 'Vacant'`.
  - Removed `|| (idx === 0 && !t.subtitle?.includes('-'))` so past tenants are never falsely marked `isCurrent` or highlighted red.
  - Added unit test `renders grey border and Vacant badge for vacant house with past tenants (e.g. house 538)` in `tests/frontend/components/area_grid_card.test.js`.
  - Synchronized `area-grid.js` across `src/api/static/js/`, `web-net/wwwroot/js/`, and `dist/win-x64/wwwroot/js/` (0 diff).

## Verification
- Vitest: 274 passed (27 test files)
- .NET xUnit: 147 passed
- Python pytest: 43 passed
