---
status: complete
task_id: 260911-nh6
slug: clean-house-settings-modal
date: 2026-09-11
---

# Quick Task Summary: Clean Up House Settings Modal Layout & Danger Zone

**Task ID**: `260911-nh6` (QCK-22)  
**Status**: Complete  
**Date**: 2026-09-11  

---

## 1. Overview
Streamlined and reorganized the House Settings modal (`#tenant-modal`):
- Expanded dialog container width to `max-w-4xl` (896px) and removed the massive explanatory note banner (`Reallocation Priority Rules...`) from the top.
- Corrected modal title to **`House Settings: ${currentHouse} (${currentArea})`** and replaced redundant area/house subtitle with useful configuration guidance: **`Configure tenant residency timelines and house configuration`**.
- Strictly enforced that **only one tenant can be marked Present at a time**: checking a tenant as Present automatically unchecks any other tenant and re-enables their end date input; adding new rows while a tenant is active defaults to not present; save validation prevents multi-present states.
- Removed the redundant outer box around the Present checkbox, leaving a clean, standard, unobstructed checkbox.
- Removed Arabic from action buttons (`Add Tenant`, `Save Changes`, `Cancel`) for clean, uncluttered controls.
- Replaced bloated, oversized individual card boxes around each tenant row with a single, elegant table container (`border border-slate-200 rounded-xl overflow-hidden`) and subtle row dividers (`divide-y divide-slate-100 py-2 px-4`).
- Solved crowding between Present status and Delete action by dedicating distinct centered column cells with a generous 16px column gap (`gap-4` in `sm:grid-cols-12`).
- Replaced the Danger Zone text with clean Arabic deletion instructions aligned directly underneath the title (`حذف هذا المنزل نهائياً مع كافة المستأجرين والوثائق والملفات من القرص. لا يمكن التراجع عن هذا الإجراء.`), and removed trailing ellipsis from the button (`Delete House`).
- Refactored individual tenant rows:
  - Removed repetitive uppercase labels (`NAME / الاسم`, `START DATE`, `END DATE`) inside rows.
  - Added compact sequential numbering badges (`.tenant-row-number`: `1`, `2`, `3`) with automatic re-indexing via `updateRowNumbers()`.
- Clarified trigger button title in the document list header to `House Settings • إعدادات المنزل`.

## 2. Changes Made
1. **`src/api/static/index.html`**:
   - Upgraded `#tenant-modal` container to `max-w-4xl` with generous padding.
   - Set title to `House Settings` and subtitle to `Configure tenant residency timelines and house configuration`.
   - Formatted Danger Zone with aligned Arabic explanation and clean `Delete House` button (no dots).
   - Streamlined buttons to clean English (`Add Tenant`, `Save Changes`, `Cancel`).
   - Integrated single table container with `sm:grid-cols-12 gap-4` column headers.
   - Bumped cache bust version to `?v=260911-33`.
2. **`src/api/static/js/tenant-manager.js`**:
   - Updated `openTenantModal()` to set title (`House Settings: ${currentHouse} (${currentArea})`) and subtitle (`Configure tenant residency timelines and house configuration`).
   - Enforced single active present tenant: checking Present unchecks all other rows and enables their end date input.
   - Defaulted newly added rows to not present if an active tenant already exists.
   - Removed outer bordered box around Present checkbox.
   - Dedicated separate columns for Name (`sm:col-span-4`), Start Date (`sm:col-span-3`), End Date (`sm:col-span-3`), Present (`sm:col-span-1`), and Delete (`sm:col-span-1`).
   - Added `updateRowNumbers()` helper to keep row indices sequential on add and remove.
3. **Tri-Directory Asset Parity**:
   - Synchronized `index.html` and `tenant-manager.js` across `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/` with 0 diff.
4. **Automated Test Coverage**:
   - Updated `tests/frontend/components/house_settings_modal.test.js` (6 tests) verifying banner removal, title and subtitle, single-present exclusivity toggle, English-only button labels, sequential row numbering, row removal re-indexing, and properly aligned Danger Zone instructions.
   - Updated `tests/frontend/test_v11_e2e_db.py` to assert `House Settings: 101 (Safra C)`.

## 3. Verification
- Vitest Frontend Suite: 170 passed across 18 files.
- Playwright E2E Suite (`test_v11_e2e_db.py`): 13 passed in 16.60s.
- Python Backend API Tests: 14 passed in `test_tenant_reallocation_api.py` and `test_tenant_repository_unit.py`.
- ASP.NET Core xUnit Suite: 85 passed.
- Static Asset Parity: `diff -ru` = 0 across all three directories.
