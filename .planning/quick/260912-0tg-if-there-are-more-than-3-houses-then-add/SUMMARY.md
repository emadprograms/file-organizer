---
status: complete
date: 2026-09-12
task: if-there-are-more-than-3-houses-then-add
commit: 35bf9df
---

# Quick Task Summary: Add Scrollbar to House Card When More Than 3 Tenancies / Houses

## User Requirement
"if there are more than 3 houses then add a scrollbar in the house card."

## Implementation Details
1. **Conditional Scrollbar Styling**:
   - In `renderAreaGrid` in `area-grid.js`, checked if `tenants.length > 3`.
   - When more than 3 records exist, added `max-h-[118px] overflow-y-auto pr-1` to `.tenants-overview-section`.
   - This keeps cards compact and uniformly sized across grid rows without vertical distortion.
2. **Scrollbar Click Protection**:
   - Added click event handler to `.tenants-overview-section` that stops click propagation if `e.offsetX > e.currentTarget.clientWidth`. This ensures dragging or clicking the vertical scrollbar track/thumb does not inadvertently trigger house navigation.
3. **Asset Synchronization & Cache Busting**:
   - Synchronized changes to `web-net/wwwroot/js/area-grid.js` and `dist/win-x64/wwwroot/js/area-grid.js`.
   - Bumped cache buster query string in all `index.html` files to `area-grid.js?v=260912-01`.
4. **Unit Tests**:
   - Created `tests/frontend/components/area_grid_card.test.js` validating that cards with <= 3 records have no scrollbar classes, cards with > 3 records have `max-h-[118px] overflow-y-auto pr-1`, and scrollbar clicks do not bubble navigation.

## Affected Files
- `src/api/static/js/area-grid.js`
- `src/api/static/index.html`
- `web-net/wwwroot/js/area-grid.js`
- `web-net/wwwroot/index.html`
- `dist/win-x64/wwwroot/js/area-grid.js`
- `dist/win-x64/wwwroot/index.html`
- `tests/frontend/components/area_grid_card.test.js`

## Verification
- Vitest Component Suite: 20 test files, 179 tests passed (0 failures).
