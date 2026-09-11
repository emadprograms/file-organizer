# Quick Plan: Add Scrollbar to House Card When More Than 3 Tenancies / Houses

## User Requirement
"if there are more than 3 houses then add a scrollbar in the house card."

Inside the `.house-card` component on the Area Grid overview, each house displays its list of tenancies / resident records (`.tenants-overview-section`). When a house has more than 3 records, the card expands vertically, causing uneven grid heights. Adding a scrollbar (`max-h-[118px] overflow-y-auto pr-1`) when `tenants.length > 3` preserves a uniform, compact card height across the grid while allowing full browsing of all records.

## Affected Files
- `src/api/static/js/area-grid.js`
- `web-net/wwwroot/js/area-grid.js`
- `dist/win-x64/wwwroot/js/area-grid.js`
- `tests/frontend/components/area_grid_card.test.js`

## Tasks

### Task 1: Update `area-grid.js` with Conditional Scrollbar for > 3 Tenancies
- Check `tenants.length > 3`.
- Conditionally apply `max-h-[118px] overflow-y-auto pr-1` to `.tenants-overview-section`.
- Prevent accidental house navigation when interacting with the scrollbar (`e.offsetX > e.currentTarget.clientWidth`).
- Propagate changes to `web-net/wwwroot/js/area-grid.js` and `dist/win-x64/wwwroot/js/area-grid.js`.

### Task 2: Add Frontend Unit Tests
- Create `tests/frontend/components/area_grid_card.test.js` to verify:
  - 1-3 tenants: No scrollbar class applied.
  - > 3 tenants: `max-h-[118px]` and `overflow-y-auto` classes applied.
  - Scrollbar click does not trigger `openHouseFromGrid`.
- Run `npm run test:frontend` and python tests.
