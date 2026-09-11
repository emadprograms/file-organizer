# Quick Plan: Streamline House Overview Cards in Area Grid

## User Requirements
1. Remove bottom section: `📄 Total Archive` and `${totalDocs} Docs`.
2. Remove `Current` badge from recent tenant; the green background highlight already indicates this.
3. Remove `🟢` and `⚪` circles from tenant rows; the green highlight and dates already distinguish current vs past.
4. Remove written tenure duration (`< 5 Yrs`, `5–10 Yrs`, `> 10 Yrs`) since the color border already indicates it and colors are explained in the area header.
5. Remove `👥 Tenants Overview` section title.
6. Move `${tenants.length} Tenants` label to the top right of the card where the tenure duration badge previously was.

## Affected Files
- `src/api/static/js/area-grid.js`
- `web-net/wwwroot/js/area-grid.js`
- `dist/win-x64/wwwroot/js/area-grid.js`
- `tests/frontend/test_tenants_overview_grid.py`
- `tests/frontend/test_grid_view.py`

## Implementation Steps
1. Modify `renderAreaGrid` in `src/api/static/js/area-grid.js`:
   - Replace top-right `tenure-badge` with `tenants-count` (`${tenants.length} ${tenants.length === 1 ? 'Tenant' : 'Tenants'}`).
   - Remove `👥 Tenants Overview` and header row from `tenants-overview-section`.
   - Remove `dotColor` (`🟢`/`⚪`) and `statusBadge` (`Current`/`Past`) from tenant rows in `tenantsHtml`.
   - Remove bottom `Total Archive` / `${totalDocs} Docs` footer.
2. Synchronize `src/api/static/js/area-grid.js` to `web-net/wwwroot/js/area-grid.js` and `dist/win-x64/wwwroot/js/area-grid.js`.
3. Update Playwright assertions in `test_tenants_overview_grid.py` and `test_grid_view.py`.
4. Verify all tests pass (`npm run test:frontend`, pytest, and dotnet test).
5. Generate SUMMARY.md and update STATE.md.
