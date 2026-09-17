---
status: resolved
trigger: "when viewing house cards, when it gets crowded, the house number becomes ... the house number should always be visible."
created: 2026-09-17
updated: 2026-09-17
---

## Current Focus
- status: resolved
- resolution: "Removed truncate from house card h3 and added flex-shrink-0 whitespace-nowrap. Converted the tenants-count badge to min-w-0 truncate with title tooltip fallback and gave the left header section flex-1 min-w-0, guaranteeing the house number identifier remains 100% visible and un-truncated even when the card header is crowded."

## Symptoms
1. **Expected behavior**: In Area Overview mode (`#area-grid-container`), the house number (`🏠 ${house.name}`) in each `.house-card` header must always remain fully visible and never truncate into an ellipsis (`...`), regardless of how crowded the card header becomes (e.g. narrow columns, open sidebars, long applicant/tenant badge labels, integrity compliance badges, and tenure badges).
2. **Actual behavior**: When the card layout or viewport was narrow or crowded, the browser prioritized fixed-width or `flex-shrink-0` badges (such as `.tenants-count`, integrity badges, and tenure badges), compressing the `<h3>` header which had the `truncate` class and no `flex-shrink-0`, causing `🏠 552` to truncate to `...` or `🏠 ...`.
3. **Error messages**: None (CSS flexbox layout and text truncation issue).
4. **Timeline**: Resolved in this session.
5. **Reproduction**: View houses in a dense area grid on small/medium screens or with sidebars expanded. When the card width decreases, the house number header (`<h3>`) was truncated with an ellipsis while badge elements took priority.

## Root Cause
In `src/HousingApplication.Web/wwwroot/js/area-grid.js` (lines 1062–1075):
- The `.house-card` header markup was:
  ```html
  <div class="flex items-center justify-between gap-2 pb-2.5 mb-2.5 border-b border-slate-100 dark:border-slate-800 flex-shrink-0">
      <div class="flex items-center gap-2 min-w-0">
          <h3 class="font-bold text-slate-900 dark:text-slate-100 text-sm group-hover:text-blue-600 transition-colors truncate" title="${house.name}">
              🏠 ${house.name}
          </h3>
          <span class="tenants-count text-[10px] font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full border border-slate-200 dark:border-slate-700 flex-shrink-0">
              ${countBadgeText}
          </span>
      </div>
      <div class="flex items-center gap-1.5 flex-shrink-0">
          ${integrityBadgeHtml}
          <span class="tenure-badge text-[10px] px-2 py-0.5 rounded border flex-shrink-0 ${badgeClass}">${badgeLabel}</span>
      </div>
  </div>
  ```
- The right badges (`integrityBadgeHtml` and `tenure-badge`) had `flex-shrink-0`.
- Inside the left container, the `.tenants-count` badge had `flex-shrink-0` and displayed long text (e.g. `"1 Tenant • 1 Applicant"`).
- Meanwhile, the `<h3>` element holding the house number/identifier had class `truncate` without `flex-shrink-0`.
- Under flex layout shrinking rules, when the card's available width became constrained, the only element in the left container allowed to shrink was the `<h3>`, turning the house number into `...`.

## Key Changes
1. **Frontend Component (`src/HousingApplication.Web/wwwroot/js/area-grid.js` & `dist/win-x64/wwwroot/js/area-grid.js`)**:
   - In `createHouseCard`:
     - Changed `h3` class: removed `truncate`, added `flex-shrink-0 whitespace-nowrap`. The house number identifier is now completely locked against shrinking or truncating.
     - Changed `.tenants-count`: replaced `flex-shrink-0` with `min-w-0 truncate` and added `title="${countBadgeText}"`. When horizontal space is tight, the secondary count badge will gracefully truncate with an ellipsis while retaining full text in its hover tooltip.
     - Changed the left container from `flex items-center gap-2 min-w-0` to `flex items-center gap-1.5 min-w-0 flex-1`.
2. **Testing & Verification (`tests/web/components/area_grid_card.test.js`)**:
   - Added test: `"ensures house number never truncates in crowded card header and delegates truncation to tenant count"`.
   - Asserts `h3` has `flex-shrink-0` and `whitespace-nowrap`, and does NOT have `truncate`.
   - Asserts `.tenants-count` has `truncate` and `min-w-0`, does NOT have `flex-shrink-0`, and includes `title` attribute.
   - All 13 tests in `area_grid_card.test.js` and all 27 tests in `house_sort.test.js` & `grid_view_options.test.js` pass with zero failures.
