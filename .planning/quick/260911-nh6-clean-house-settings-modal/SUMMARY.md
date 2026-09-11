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
- Simplified modal title to `Manage Tenants: ${currentHouse} (${currentArea})` and subtitle to `${currentArea} • House ${currentHouse}`, eliminating wall-of-text boilerplate.
- Removed Arabic from action buttons (`Add Tenant` and `Save Changes`) for clean, uncluttered controls.
- Replaced bloated, oversized individual card boxes around each tenant row with a single, elegant table container (`border border-slate-200 rounded-xl overflow-hidden`) and subtle row dividers (`divide-y divide-slate-100 py-2 px-4`).
- Solved crowding between Present status and Delete action by dedicating distinct centered column cells with a generous 16px column gap (`gap-4` in `sm:grid-cols-12`).
- Completely removed the gray boilerplate sentence in the Danger Zone area (`Permanently delete this house, along with all associated tenants, documents, and disk folders. This action cannot be undone.`), keeping a minimal danger card with `Delete House • حذف المنزل` and a clean `Delete House...` trigger button.
- Refactored individual tenant rows:
  - Removed repetitive uppercase labels (`NAME / الاسم`, `START DATE`, `END DATE`) inside rows.
  - Added compact sequential numbering badges (`.tenant-row-number`: `1`, `2`, `3`) with automatic re-indexing via `updateRowNumbers()`.
  - Added sleek present checkbox badge (`.tenant-present-badge`) with live status toggle styling.
- Clarified trigger button title in the document list header to `House Settings • إعدادات المنزل`.

## 2. Changes Made
1. **`src/api/static/index.html`**:
   - Upgraded `#tenant-modal` container to `max-w-4xl` with generous padding.
   - Removed top priority rules note banner and redundant grey explanatory paragraph in Danger Zone.
   - Streamlined buttons to clean English (`Add Tenant`, `Save Changes`, `Cancel`).
   - Integrated single table container with `sm:grid-cols-12 gap-4` column headers.
   - Bumped cache bust version to `?v=260911-30`.
2. **`src/api/static/js/tenant-manager.js`**:
   - Updated `openTenantModal()` to set concise title (`Manage Tenants: ${currentHouse} (${currentArea})`) and subtitle (`${currentArea} • House ${currentHouse}`).
   - Dedicated separate columns for Name (`sm:col-span-4`), Start Date (`sm:col-span-3`), End Date (`sm:col-span-3`), Present (`sm:col-span-1`), and Delete (`sm:col-span-1`).
   - Replaced thick card borders per row with slim rows (`py-2 px-4 hover:bg-slate-50/60`).
   - Updated button feedback to concise English (`Saving...` / `Save Changes`).
   - Added `updateRowNumbers()` helper to keep row indices sequential on add and remove.
3. **Tri-Directory Asset Parity**:
   - Synchronized `index.html` and `tenant-manager.js` across `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/` with 0 diff.
4. **Automated Test Coverage**:
   - Updated `tests/frontend/components/house_settings_modal.test.js` (5 tests) verifying banner removal, clean title and subtitle, English-only button labels, sequential row numbering, row removal re-indexing, present toggle behavior, and absence of the gray boilerplate text.

## 3. Verification
- Vitest Frontend Suite: 169 passed across 18 files.
- Playwright E2E Suite (`test_v11_e2e_db.py`): 13 passed in 16.60s.
- Python Backend API Tests: 14 passed in `test_tenant_reallocation_api.py` and `test_tenant_repository_unit.py`.
- ASP.NET Core xUnit Suite: 85 passed.
- Static Asset Parity: `diff -ru` = 0 across all three directories.
