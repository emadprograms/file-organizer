---
status: complete
date: 2026-09-11
task_id: 260911-nj6
---

# Quick Task Summary: Merge Area Overview Headers into Single Top Bar

## Overview
Eliminated the redundant secondary header bar inside `#area-grid-panel` and consolidated its controls into the primary application navbar (`#top-navbar`).

## Changes
1. **`src/api/static/index.html`**:
   - Relocated `#grid-area-stats` badge to the top navbar next to `#current-house-title`.
   - Added `#grid-area-title` as an invisible tracking span to maintain selector contract for existing test fixtures.
   - Moved `#grid-tenure-legend` (`< 5y | 5–10y | > 10y`) and `#open-add-house-modal-btn` (`+ إضافة منزل جديد`) into the top navbar actions container.
   - Removed the lower sub-header bar container above `#area-grid-container` entirely, allowing house cards to start cleanly below the main navbar.
2. **`src/api/static/js/area-grid.js`**:
   - Updated `renderAreaGrid` to display `#grid-area-stats`, `#grid-tenure-legend`, and `#open-add-house-modal-btn` in the navbar when entering area overview mode.
   - Updated `openHouseFromGrid` to cleanly hide area-overview-specific navbar elements when entering a house.
3. **`src/api/static/js/router.js`**:
   - In `switchToViewMode('db')` and `selectHouse`, ensured `#grid-area-stats`, `#grid-tenure-legend`, and `#open-add-house-modal-btn` are hidden.
4. **Synchronized Frontends**:
   - Mirror updated `index.html`, `area-grid.js`, and `router.js` to `web-net/wwwroot/` and `dist/win-x64/wwwroot/`.
5. **Verification**:
   - `npm run test:frontend`: 14 passed (148 tests passed).
   - `.venv/bin/pytest tests/frontend/test_grid_view.py tests/frontend/test_tenants_overview_grid.py`: 11 passed in 10.22s.
   - `.venv/bin/pytest tests/test_api.py`: 9 passed.
