---
status: complete
date: 2026-09-11
task_id: 260911-j4x
commit: 33a31da
---

# Quick Task 260911-j4x: Change Current Tenant Highlight to Blue

## Overview
Switched current tenant highlight and icon styling on house cards from emerald green to brand blue (`bg-blue-50/70 border-blue-200/80` and `bg-blue-100 text-blue-700`). This completely resolves the color clash and semantic overloading with the `< 5 Yrs` green tenure badge.

## Changes Made
- `src/api/static/js/area-grid.js`: Updated `cardBg` and `tenantIcon` for current/residing tenants to blue theme.
- `web-net/wwwroot/js/area-grid.js`: Synchronized frontend code.
- `src/api/static/index.html` & `web-net/wwwroot/index.html`: Bumped cache-buster query string to `?v=260911-19`.
- `tests/frontend/test_tenants_overview_grid.py`: Updated assertion checking current tenant item class to `bg-blue-50`.

## Verification
- Vitest: 144 passed (13 test files)
- Playwright: 11 passed in 13.53s (`test_grid_view.py`, `test_tenants_overview_grid.py`)
- .NET xUnit: 84 passed
