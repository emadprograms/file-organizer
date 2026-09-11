---
status: complete
date: 2026-09-11
task_id: 260911-jhn
commit: 13d0246
---

# Quick Task 260911-jhn: Harmonize Document Action Colors Between 3-Dot Menu and Multi-Select Bar

## Overview
Harmonized document operation colors between the 3-dot dropdown menu and the floating multi-select batch action bar, ensuring identical semantic color association across the application:
- 🟠 **Move**: Amber/Orange (`bg-amber-600` batch button, `text-amber-500` / `hover:bg-amber-50` 3-dot item, amber modal theme)
- 🟣 **Copy**: Indigo/Purple (`bg-indigo-600` batch button, `text-indigo-500` / `hover:bg-indigo-50` 3-dot item, indigo modal theme)
- 🔴 **Delete**: Rose/Red (`bg-rose-600` batch button, `text-rose-500` / `hover:bg-rose-50` 3-dot item, rose modal theme)
- 🔵 **Rename**: Blue (`text-blue-500` / `hover:bg-blue-50` 3-dot item, blue inline rename border)
- 🟢 **Timeline**: Emerald (`text-emerald-500` / `hover:bg-emerald-50` 3-dot item)

Maintained uniform action title length in the 3-dot dropdown menu ("Rename Document", "Move Document", "Copy Document", "Show in Timeline", "Delete Document") to avoid visual imbalance against "Show in Timeline".

## Changes Made
- `src/api/static/index.html` & `web-net/wwwroot/index.html`:
  - Updated `#btn-batch-move` styling to `bg-amber-600 hover:bg-amber-500`.
  - Updated `#batch-move-modal` header icon (`bg-amber-50 text-amber-600 border-amber-100`), input focus rings (`focus:ring-amber-500`), and confirm button (`bg-amber-600 hover:bg-amber-700`).
  - Bumped script cache busters to `?v=260911-21`.
- `src/api/static/js/doc-manager.js` & `web-net/wwwroot/js/doc-manager.js`:
  - Updated 3-dot menu hover classes to match item icon colors (Move: amber, Copy: indigo, Timeline: emerald, Rename: blue, Delete: rose).
- `.planning/milestones/v14.0-ROADMAP.md`: Documented Quick Refinement QCK-13.
- `.planning/STATE.md`: Updated Quick Tasks Completed and Last Activity.

## Verification
- Vitest: 144 passed (13 test files)
- Playwright: 13 passed (`test_house_register.py`, `test_grid_view.py`, `test_tenants_overview_grid.py`)
- .NET xUnit: 84 passed
