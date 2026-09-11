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
4. **Dynamic Glowing Animation on Current Tenant**:
   - Implemented `.tenant-current-glow` in `css/styles.css` using a high-performance rotating `conic-gradient` border beam (`@keyframes glow-border-beam`) with an inner emerald mask (`#ecfdf5`).
   - The light beam continuously and subtly travels around the rectangle perimeter of the current tenant, providing an intuitive, dynamic visual indicator without clutter.
   - Removed redundant `Current` and `Past` badges and emoji circles (`🟢`/`⚪`) as requested.
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
- Python & .NET live servers restarted with cache-busting version `?v=260911-16`.
