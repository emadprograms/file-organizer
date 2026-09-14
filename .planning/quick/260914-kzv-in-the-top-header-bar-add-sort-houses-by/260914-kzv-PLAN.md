# Quick Task 260914-kzv: In top header bar, add sort houses by house number or longest tenant stay

**Task:** Add house sorting controls in the top header bar allowing users to sort houses by House Number or Longest Tenant Stay.
**Directory:** .planning/quick/260914-kzv-in-the-top-header-bar-add-sort-houses-by

## User Requirements
- In the top header bar (`#top-navbar`), add a "Sort Houses By" control.
- Support sorting houses by:
  1. House number (natural numeric order: 1, 2, 10, 101, 616...).
  2. Longest tenant stay (descending: houses with the longest resident tenant stay first).
- Integrate seamlessly with light and dark mode design system.
- Control visibility: visible in Area Overview mode alongside `#grid-tenure-legend`, hidden when viewing individual houses or in DB mode.
- Maintain 100% byte parity between `src/` and `dist/`.
- Full automated test coverage.

## Tasks

### Task 1: Add Sort Control to Top Navbar in `index.html` & Styles
- Add `#grid-house-sort-container` with `#grid-house-sort-select` inside `#top-navbar` (next to `#grid-tenure-legend`).
- Style cleanly with icon, label ("Sort:"), and options: "House Number" and "Longest Stay".
- Ensure dark mode and light mode styling matches existing navbar controls.

### Task 2: Implement Sorting Logic in `area-grid.js` & Wire Router Visibility
- Implement `compareHouseNumbers(a, b)` using natural numeric comparison.
- Implement `getHouseMaxStay(house)` and `compareHouseLongestStay(a, b)`.
- Persist chosen sort mode in `localStorage` (`'house_sort_by'`).
- In `renderAreaGrid(areaNode)`, sort houses according to active sort preference before rendering cards.
- Wire `onchange` on `#grid-house-sort-select` to re-render the area grid immediately upon selection.
- Ensure `#grid-house-sort-container` is shown in `renderAreaGrid` and hidden in `openHouseFromGrid`, `router.js` (`switchToViewMode`, `loadHouseProfile`).
- Export sorting helper functions for unit test verification.

### Task 3: Automated Tests & Distribution Parity
- Add comprehensive unit tests in `tests/web/components/house_sort.test.js` verifying:
  - Navbar HTML structure and options.
  - Natural house number sorting (e.g. 2 before 10, 101 before 616).
  - Longest tenant stay sorting (houses with 30y stay before 5y stay, vacant last).
  - Dropdown change triggers re-render and persists to `localStorage`.
  - Dynamic visibility in Area Overview vs House Detail vs DB mode.
- Update `tests/web/components/unified_header.test.js` if necessary.
- Sync `src/` to `dist/win-x64/wwwroot/` and verify 0 diff.
- Run `npm test` and `dotnet test`.
