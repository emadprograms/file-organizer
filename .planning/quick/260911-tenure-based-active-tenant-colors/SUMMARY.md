---
status: complete
date: 2026-09-11
task_id: 260911-tenure-colors
slug: tenure-based-active-tenant-colors
---

# Quick Task 260911-tenure-colors: Tenure-Based Active Tenant Colors in Tenant Selection & House Overview

## Overview
Replaced the bland hardcoded brand blue highlight for active/residing tenants in the tenant selection area (`house-profile.js`) and house overview cards (`area-grid.js`) with dynamic tenure-based colors directly aligned with the house overview duration standards:
- **< 5 years** (`short`): Emerald Green (`border-emerald-200 bg-emerald-50/40`, `bg-emerald-100 text-emerald-700`, `border-emerald-300 bg-emerald-100 text-emerald-800`, dot `bg-emerald-500`, option emoji `🟢`)
- **5–10 years** (`medium`): Amber Yellow (`border-amber-200 bg-amber-50/40`, `bg-amber-100 text-amber-700`, `border-amber-300 bg-amber-100 text-amber-800`, dot `bg-amber-500`, option emoji `🟡`)
- **> 10 years** (`long`): Rose Red (`border-rose-200 bg-rose-50/40`, `bg-rose-100 text-rose-700`, `border-rose-300 bg-rose-100 text-rose-800`, dot `bg-rose-500`, option emoji `🔴`)
- **Past tenants**: Clean slate neutral (`border-slate-200 bg-white`, `bg-slate-100 text-slate-500`, `border-slate-200 bg-slate-100 text-slate-600`, dot `bg-slate-400`, option emoji `👤`).

## Changes Made
- `src/api/models.py` & `src/api/routes.py`: Added `duration_category: Optional[str] = None` to `HouseTenantProfile` and computed from `y_int` duration years.
- `web-net/Models/DTOs.cs` & `web-net/Data/FileOrganizerRepository.cs`: Added `DurationCategory` to `HouseTenantProfileDto` and computed from duration years in `GetHouseProfileAsync`.
- `src/api/static/js/house-profile.js`:
  - Added `getTenantTenureCategory(t)` helper with fallback logic extracting tenure duration from `start_date`/`end_date` or `duration_str_ar`.
  - Added `TENURE_THEMES` dictionary providing theme classes for `short` (emerald), `medium` (amber), and `long` (rose).
  - Dynamically styled the active tenant card, avatar icon, and `حالي` badge in the Tenancy Register according to tenure category.
  - Updated the Export Archive modal tenant dropdown option emoji (`🟢`, `🟡`, `🔴`, `👤`) according to active tenure.
- `src/api/static/js/area-grid.js`:
  - Dynamically styled current tenant card background (`currentCardBg`) and icon (`currentIconBg`) according to `durCat` (`short` -> emerald green, `medium` -> amber yellow, `long` -> rose red) instead of hardcoded blue.
- `src/api/static/js/categories-view.js`:
  - Changed `.folder-select-checkbox` attribute to `data-folder-category` so Playwright strict locators on `[data-category-name='...']` match only the category card.
- Synchronized all assets to `web-net/wwwroot/js/` and `dist/win-x64/wwwroot/js/` with zero static diff.
- `tests/frontend/components/house_profile.test.js`: Added unit tests verifying tenure color assignments for `< 5 Yrs` (emerald), `5–10 Yrs` (amber), and `> 10 Yrs` (rose).
- `tests/frontend/test_tenants_overview_grid.py`: Updated current tenant row assertion to verify `bg-emerald-50` for `< 5 Yrs` tenure.

## Verification
- Vitest Component Suite: 145 passed across 13 test files (100% pass rate).
- Playwright Browser E2E Suite: 49 passed (100% pass rate).
- ASP.NET Core xUnit Suite: 84 passed (100% pass rate).
- Python Pytest Backend Suite: 32 passed (100% pass rate).
- Zero static asset diff between `src/api/static/` and `web-net/wwwroot/`.
