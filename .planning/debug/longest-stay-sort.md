---
status: resolved
trigger: "the longest stay isn't working properly."
created: 2026-09-14
updated: 2026-09-14
---

# Debug Session: longest-stay-sort

## Symptoms
- **Expected behavior**: Sorting houses by "Longest Stay" should order houses by their active residing tenant's tenure in descending order (e.g. houses occupied for decades / `> 10 Yrs` rose badge, followed by `5–10 Yrs` amber badge, `< 5 Yrs` emerald badge, and finally vacant houses), matching the house card tenure badges and active resident stay.
- **Actual behavior**: Sorting by "longest stay" was reported by the user as not working properly. Green `< 5 Yrs` cards and vacant houses with ancient historical tenants were jumping above long-standing active residents.
- **Error messages**: None (silent logical misordering).
- **Timeline**: Introduced when "Sort houses by" dropdown was implemented in `bb07b19`.
- **Reproduction**: In the top header bar of the Area Grid, select "Longest Stay" from the house sort dropdown.

## Resolution
- **root_cause**: 
  1. In `area-grid.js`, `getHouseMaxStayDays` previously looped through all tenants in `house.children` (including past tenants from decades ago) and computed tenure using `Math.max` across all of them. This meant a house occupied by a new tenant who moved in 6 months ago (showing a green `< 5 Yrs` badge) with a past resident from 1980–2010 (30 years) received a tenure calculation of 30 years and jumped to the very top of the grid above active resident tenants with 15-year tenures.
  2. Vacant houses with old past tenants also received multi-decade tenure calculations and were ranked at the top of the grid above active tenants.
  3. `parseYearOrDate(tenant.end_date, true)` defaulted missing or null end dates on past tenants to `new Date()`, erroneously calculating departed tenants as still residing until today.
  4. Date parsing did not account for `DD/MM/YYYY` or `DD-MM-YYYY` formats or Arabic tenure strings, occasionally causing fallback to January 1 or zero.
- **fix**:
  1. Updated `isTenantActive` and `getHouseActiveStayDays` in `src/HousingApplication.Web/wwwroot/js/area-grid.js` to strictly anchor house tenure to current residing tenants matching `house.current_tenant`, `isTenantActive(t)`, `house.subtitle` (e.g. `Since 1990 (36y)`), and `house.duration_category`.
  2. Updated `compareHouseLongestStay` to enforce that occupied houses always sort before vacant houses.
  3. Updated `parseYearOrDate` to parse ISO dates, `DD/MM/YYYY`, `DD-MM-YYYY`, 4-digit years, and Arabic keywords (`الآن`, `بدء الإيجار`).
  4. Updated vacant house comparison to sort among vacant houses by longest past stay, falling back to natural numeric house number tie-breaking.
  5. Synchronized `src/HousingApplication.Web/wwwroot/js/area-grid.js` to `dist/win-x64/wwwroot/js/area-grid.js` maintaining 100% byte parity.
- **verification**:
  - Added 4 new automated unit tests in `tests/web/components/house_sort.test.js` validating that active resident tenure is prioritized over past tenants, vacant houses always sort after occupied houses, subtitle/duration_category fallbacks work, and Arabic dates are handled properly.
  - All 16 house sort tests passed.
  - Full test suites passed: 397 Vitest tests (34 test files) and 925 .NET tests.
- **files_changed**:
  - `src/HousingApplication.Web/wwwroot/js/area-grid.js`
  - `dist/win-x64/wwwroot/js/area-grid.js`
  - `tests/web/components/house_sort.test.js`
  - `.planning/debug/longest-stay-sort.md`
