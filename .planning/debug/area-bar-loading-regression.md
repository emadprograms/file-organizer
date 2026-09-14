---
status: investigating
trigger: "the code has regressed. the area bar just keeps showing loading and I cannot click on the house card to oepn it. make tests to catch errors like these in the future."
created: 2026-09-14T13:13:00Z
updated: 2026-09-14T13:17:00Z
---

## Current Focus
- hypothesis: "In router.js handleHashChange(), an unnecessary call to window.loadAreaGrid(areaId) triggers window.loadTree() in area-grid.js. When loadTree() in sidebar.js completes, it calls window.handleHashChange(), causing an infinite asynchronous recursion loop. This loop keeps isTreeLoading set to true (causing the area bar / sidebar to continuously display Loading...), floods the network with /api/tree requests, and continually re-creates house card DOM elements so clicks cannot open houses."
- test: "Check router.js line 136, area-grid.js loadAreaGrid(), and sidebar.js loadTree() call chain. Remove the recursive call, add re-entrancy guard in sidebar.js, and verify loadTree and house card navigation in automated tests."
- expecting: "Area bar loads once, displays areas cleanly, stops showing Loading..., and house cards can be clicked to open houses without infinite re-render."
- next_action: "Apply fix in router.js, app.js, and sidebar.js, replicate to dist, and write regression test suite."

## Symptoms
- **Expected Behavior**: Visiting or navigating to an area (`#/area/{areaId}`) should render the sidebar areas cleanly, display the house cards in the Area Grid, and allow clicking any house card to navigate to its house profile view.
- **Actual Behavior**: The sidebar ("area bar") remains permanently stuck on "Loading...", and house cards cannot be clicked to open.
- **Error Messages**: Perpetual async loop continuously fetching `/api/tree` and re-rendering sidebar and grid cards.
- **Timeline**: Introduced when `loadAreaGrid` was called inside `handleHashChange()` in `router.js` in commit `8335e65`.
- **Reproduction**: Load the application or navigate to any area route (`#/area/Safra%20C`). Observe that the sidebar shows "Loading..." and cards cannot be opened.
