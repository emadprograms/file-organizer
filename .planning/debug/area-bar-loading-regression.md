---
status: resolved
trigger: "the code has regressed. the area bar just keeps showing loading and I cannot click on the house card to oepn it. make tests to catch errors like these in the future."
created: 2026-09-14T13:13:00Z
updated: 2026-09-14T13:23:00Z
---

## Resolution Summary
- **Root Cause**: In commit `8335e65`, `src/HousingApplication.Web/wwwroot/js/router.js` had `window.loadAreaGrid(areaId)` added inside `handleHashChange()` on the area route (`areaId && !houseId`). `loadAreaGrid(areaId)` calls `await window.loadTree()`. In `sidebar.js`, `loadTree()` sets `isTreeLoading = true; renderSidebar();` (displaying `<p>Loading...</p>` in `#house-list`). When `/api/tree` resolves, `loadTree()` sets `isTreeLoading = false; renderSidebar();` and then calls `window.handleHashChange()`. Because `handleHashChange()` invoked `loadAreaGrid(areaId)`, which called `loadTree()`, which called `handleHashChange()`, this produced an infinite asynchronous recursive loop. As a result:
  1. `isTreeLoading` was continually toggled back to `true`, leaving the area sidebar stuck on "Loading...".
  2. `renderAreaGrid()` was repeatedly clearing and reconstructing `#area-grid-container` every ~20ms (`houseCardsContainer.innerHTML = ''`), destroying DOM elements under user clicks so house cards could not open.
- **Fix Applied**:
  1. Removed `window.loadAreaGrid(areaId)` from `router.js` (`selectAreaGrid(areaNode)` already renders the area grid synchronously without re-fetching tree data).
  2. Removed redundant `window.loadAreaGrid(currentArea)` from `app.js` (`backToGridBtn` listener).
  3. Added an `activeLoadPromise` concurrency and re-entrancy guard in `sidebar.js` (`if (activeLoadPromise) return activeLoadPromise;`) so multiple or concurrent calls to `loadTree()` return the existing in-flight promise.
  4. Corrected tenant overflow length check in `area-grid.js` (`orderedTenants.length > 3`).
  5. Kept 100% byte parity between `src/HousingApplication.Web/wwwroot/` and `dist/win-x64/wwwroot/`.
- **Regression Tests Added**:
  - `tests/web/components/area_navigation_regression.test.js`:
    1. Verifies tree data is loaded once and never enters an infinite recursive loop on area navigation.
    2. Verifies clicking house cards navigates cleanly to house profile without interference or re-renders.
    3. Verifies concurrency / re-entrancy protection in `loadTree()` via `activeLoadPromise`.
    4. Verifies navigating back to grid does not trigger an infinite reload storm.
  - All 365 Vitest web tests passing across 32 test files.
  - All 925 .NET xUnit tests passing.

## Symptoms
- **Expected Behavior**: Visiting or navigating to an area (`#/area/{areaId}`) should render the sidebar areas cleanly, display the house cards in the Area Grid, and allow clicking any house card to navigate to its house profile view.
- **Actual Behavior**: The sidebar ("area bar") remains permanently stuck on "Loading...", and house cards cannot be clicked to open.
- **Error Messages**: Perpetual async loop continuously fetching `/api/tree` and re-rendering sidebar and grid cards.
- **Timeline**: Introduced when `loadAreaGrid` was called inside `handleHashChange()` in `router.js` in commit `8335e65`.
- **Reproduction**: Load the application or navigate to any area route (`#/area/Safra%20C`). Observe that the sidebar shows "Loading..." and cards cannot be opened.
