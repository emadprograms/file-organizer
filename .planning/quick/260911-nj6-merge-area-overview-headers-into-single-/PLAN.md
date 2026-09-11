# Quick Task Plan: Merge Area Overview Headers into Single Top Bar

**Task ID**: `260911-nj6`  
**Description**: Merge area overview headers into single top bar and remove redundant lower header  
**Date**: 2026-09-11  

---

## 1. Problem Statement
When viewing an area in Grid Overview mode (e.g. Safra D), the app displays two stacked header bars:
1. The top application navbar (`#top-navbar`), displaying `Safra D — Houses Overview` and global tools (`⌘K`, `?`, `+`).
2. A secondary sub-header bar directly above the house cards inside `#area-grid-panel`, which repeats the area title and houses the tenure legend (`< 5y | 5–10y | > 10y`), the house count badge (`#grid-area-stats`), and the `+ إضافة منزل جديد` button (`#open-add-house-modal-btn`).

This second header bar is redundant and wastes vertical space. The user wants only one header bar, with the contents of the second header bar moved up into the first (top) header bar, and the lower header bar removed entirely.

## 2. Proposed Changes

### 1. `src/api/static/index.html`
- In `#top-navbar`:
  - In the left section, add `#grid-area-stats` badge alongside `#current-house-title` and keep `<span id="grid-area-title" class="hidden"></span>` for test compatibility.
  - In the right section, add `#grid-tenure-legend` (tenure color indicator pills) and `#open-add-house-modal-btn` (`+ إضافة منزل جديد`).
- In `#area-grid-panel`:
  - Completely remove the redundant secondary header bar (`<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 pb-4 border-b border-slate-200...">`).
  - Leave `#area-grid-container` directly inside `#area-grid-panel`.

### 2. `src/api/static/js/area-grid.js`
- In `renderAreaGrid`:
  - Show and update `#grid-area-stats`.
  - Show `#grid-tenure-legend` and `#open-add-house-modal-btn`.
  - Update `#grid-area-title` textContent as before.
- In `openHouseFromGrid`:
  - Hide `#grid-area-stats`, `#grid-tenure-legend`, and `#open-add-house-modal-btn`.

### 3. `src/api/static/js/router.js`
- In `selectHouse` and `switchToViewMode('db')`:
  - Ensure `#grid-area-stats`, `#grid-tenure-legend`, and `#open-add-house-modal-btn` are hidden when navigating to a house/tenant or database inspector view.

### 4. Synchronization & Verification
- Synchronize changes across `web-net/wwwroot/` and `dist/win-x64/wwwroot/`.
- Run frontend unit tests (`npm run test:frontend`).
- Run Playwright frontend tests (`.venv/bin/pytest tests/frontend/test_grid_view.py tests/frontend/test_tenants_overview_grid.py`).
- Create `SUMMARY.md` and commit changes.
