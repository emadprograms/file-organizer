# Quick Task Plan: Tenure-Based Active Tenant Colors (QCK-12)

**Task ID**: `260911-tenure-colors`  
**Slug**: `tenure-based-active-tenant-colors`  
**Milestone**: v14.0 Power-User Operations & Portfolio Expansion  
**Date**: 2026-09-11  

## Objective
Replace the hardcoded brand blue styling for the active/latest tenant in the tenant selection area (House Profile tenancy register) and house overview cards with dynamic tenure-based colors aligned with the house overview duration standards:
- **< 5 years** (`short`): Emerald Green (`border-emerald-200 bg-emerald-50/40`, `bg-emerald-100 text-emerald-700`, `border-emerald-300 bg-emerald-100 text-emerald-800`, `🟢`)
- **5–10 years** (`medium`): Amber Yellow (`border-amber-200 bg-amber-50/40`, `bg-amber-100 text-amber-700`, `border-amber-300 bg-amber-100 text-amber-800`, `🟡`)
- **> 10 years** (`long`): Rose Red (`border-rose-200 bg-rose-50/40`, `bg-rose-100 text-rose-700`, `border-rose-300 bg-rose-100 text-rose-800`, `🔴`)
- **Past tenants**: Clean neutral slate styling (`border-slate-200 bg-white`, `bg-slate-100 text-slate-500`, `border-slate-200 bg-slate-100 text-slate-600`, `👤`).

## Implementation Steps
1. **Backend Parity**:
   - `src/api/models.py` & `src/api/routes.py`: Add `duration_category` to `HouseTenantProfile` and compute from `y_int`.
   - `web-net/Models/DTOs.cs` & `web-net/Data/FileOrganizerRepository.cs`: Add `DurationCategory` to `HouseTenantProfileDto` and compute from duration years.
2. **Frontend Styling**:
   - `src/api/static/js/house-profile.js`: Add `getTenantTenureCategory` with fallback logic; dynamically style active card, avatar, and `حالي` badge; update export select option emoji.
   - `src/api/static/js/area-grid.js`: Style residing tenant row on house cards according to duration category (`short` -> green, `medium` -> yellow, `long` -> red).
3. **Synchronization**:
   - Synchronize JS to `web-net/wwwroot/js/` and `dist/win-x64/wwwroot/js/`.
   - Increment cache busters in `index.html` files.
4. **Test Suite Verification**:
   - Update `tests/frontend/components/house_profile.test.js` and `tests/frontend/test_tenants_overview_grid.py`.
   - Run Vitest, Playwright, xUnit, and Pytest suites.
5. **Documentation & Commit**:
   - Update `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/MILESTONES.md`, `.planning/v14.0-MILESTONE-AUDIT.md`.
   - Commit and push to `origin/main`.
