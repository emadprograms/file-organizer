---
status: complete
date: 2026-09-12
task_id: 260912-header-tenure-legend-vacant
---

# Quick Task 260912-header-tenure-legend-vacant: Header Bar Tenure Legend Vacant Indicator & Full Dark Mode Support

## Overview
The tenure duration legend in the top navigation bar (`#grid-tenure-legend`) previously displayed `< 5y` (emerald), `5–10y` (amber), and `> 10y` (rose), but omitted an indicator for vacant properties (`Vacant`), and lacked dark mode CSS utility classes for its container and dividers.

## Changes Made
- **HTML Templates (`src/api/static/index.html`, `web-net/wwwroot/index.html`, `dist/win-x64/wwwroot/index.html`)**:
  - Added the `Vacant` indicator with a neutral slate grey dot marker:
    ```html
    <span class="inline-flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-slate-400 dark:bg-slate-500"></span> Vacant</span>
    ```
  - Added dark mode classes to the legend container:
    `dark:text-slate-300 dark:bg-slate-800 dark:border-slate-700`
  - Added dark mode styling to the vertical dividers:
    `text-slate-300 dark:text-slate-600`
  - Synchronized across all 3 web root directories with 0 diff.

## Verification
- **Vitest Frontend Test**: Updated `tests/frontend/components/unified_header.test.js` to assert that `#grid-tenure-legend` contains `'Vacant'` alongside `'< 5y'`, `'5–10y'`, and `'> 10y'`.
- All 277 Vitest tests across 27 files pass.
