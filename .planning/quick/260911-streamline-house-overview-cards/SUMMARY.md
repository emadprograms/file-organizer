---
status: complete
date: 2026-09-11
task: streamline-house-overview-cards
---

# Quick Task Summary: Streamline House Overview Cards in Area Grid

## User Requirements & Implementation
1. **Added Divider Below House Number**:
   - Inserted a sleek bottom border divider (`pb-2.5 mb-2.5 border-b border-slate-100`) separating the house title header from the tenants list.
2. **Restored Tenure Badge (5-10 Yrs)**:
   - Restored `.tenure-badge` with color coding (`🟢 < 5 Yrs`, `🟡 5–10 Yrs`, `🔴 > 10 Yrs`) in the top-right corner.
3. **Moved Tenant Count Beside House Title**:
   - Positioned `.tenants-count` pill (`2 Tenants`) neatly in the header next to `🏠 ${house.name}`.
4. **Heroicon SVGs for Tenants (Man for Residing, Clock for Past)**:
   - Replaced green/grey dots and removed the light beam animation.
   - Residing/current tenant is marked with the User (man) Heroicon SVG inside an emerald pill container (`bg-emerald-100 text-emerald-700`) on a clean emerald-highlighted card (`bg-emerald-50/70 border-emerald-200/80`).
   - Past/non-residing tenants are marked with the Clock Heroicon SVG inside a slate pill container (`bg-slate-200/80 text-slate-500`) on a slate card (`bg-slate-50 border-slate-200/60`).
   - Matches the iconography of `house-profile.js` 100%.
5. **Restored Document Count at Card Bottom**:
   - Re-added the footer with `📄 Total Archive` and `.doc-count` (`${totalDocs} Docs`).

## Affected Files
- `src/api/static/js/area-grid.js`
- `src/api/static/css/styles.css`
- `src/api/static/index.html`
- `web-net/wwwroot/js/area-grid.js`
- `web-net/wwwroot/css/styles.css`
- `web-net/wwwroot/index.html`
- `tests/frontend/test_tenants_overview_grid.py`
- `tests/frontend/test_grid_view.py`

## Verification
- Vitest: 144/144 passed (`npm run test:frontend`).
- Playwright: 11/11 passed (`pytest tests/frontend/test_grid_view.py tests/frontend/test_tenants_overview_grid.py`).
- .NET xUnit: 84/84 passed (`dotnet test web-net/FileOrganizer.Tests/`).
- Python & .NET live servers restarted with cache-busting version `?v=260911-17`.
