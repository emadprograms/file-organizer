# Quick Task 260912-jf8: Vacant House Grey Styling & False Active Tenant Fallback Removal Summary

## Overview
Resolved an issue where houses without an active tenant (all past tenants vacated) erroneously fell back to treating the first past tenant as current. This forced a long-tenure calculation (> 10 Yrs, red border) and displayed the past resident on the house card. In addition, the frontend had a fallback that falsely colored past tenants, and displayed Unknown when duration category was null.

## Key Changes
1. **Backend .NET (`web-net/Data/FileOrganizerRepository.cs`)**:
   - In `GetTreeAsync`, `GetHouseCardsAsync`, and `GetHouseProfileAsync`: Removed `if (activeTenant == null && hTenants.Count > 0) activeTenant = hTenants[0];`.
   - When no tenant is active, `activeTenant`, `CurrentTenant`, and `DurationCategory` remain `null`, and `TenureColor` is set to `"grey"`.
2. **Backend Python (`src/api/routes.py`, `src/presentation/export_static.py`, `scripts/export_web.cjs`)**:
   - In `get_tree`: Removed first-tenant fallback when no active tenant exists.
   - Enforced `tenant_is_present` checking across filesystem fallback and static export scripts.
3. **Frontend (`area-grid.js`)**:
   - Styled vacant houses with a neutral grey border (`border-l-slate-300 dark:border-l-slate-600`).
   - Replaced `Unknown` tenure badge label with `Vacant` (`bg-slate-100 dark:bg-slate-800 text-slate-500`).
   - Removed `|| (idx === 0 && !t.subtitle?.includes('-'))` so past tenants are never colored as current.
   - Maintained 100% parity across `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/`.

## Verification
- 147 .NET xUnit tests passed in `web-net/FileOrganizer.Tests/`.
- 12 Pytest tests in `test_api_v11.py` passed (including `test_get_tree_vacant_house_no_active_tenant`).
- 274 Vitest tests across 27 files passed (including 4 in `area_grid_card.test.js`).
