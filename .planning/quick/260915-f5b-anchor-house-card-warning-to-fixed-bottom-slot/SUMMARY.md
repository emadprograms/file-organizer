# Quick Task: 260915-f5b Anchor House Card Missing-Docs Warning to Fixed Bottom Slot Above Footer Bar

## Overview
Anchored the missing documents warning dialog (`.missing-docs-strip`) in the House Card (`area-grid.js`) to a fixed location in the card's bottom zone (`.card-bottom-zone`), positioned directly above the card footer (`.card-footer`, which contains Total Archive docs or Latest Stay duration).

## User Problem Solved
Previously, the warning was positioned immediately below the tenant list inside the variable-height top container (`.tenants-overview-section`). Because houses have varying tenant counts (from 0 to 3+), the warning appeared at arbitrary vertical positions across houses in the grid. If a house had 1 tenant, the warning floated near the top of the card with an empty void below it. If a house had 3 tenants, it appeared much lower down. 

The user requested that every house card have a consistent, fixed location at the bottom just above the footer bar, conditioning the user's eye to immediately know:
- If that specific bottom area is empty -> The house is fine (100% compliant or vacant).
- If that specific bottom area has a warning box -> Missing documents are immediately apparent in a predictable, consistent location.

## Changes Made
1. **House Card DOM Hierarchy (`src/HousingApplication.Web/wwwroot/js/area-grid.js` & `dist/win-x64/wwwroot/js/area-grid.js`)**:
   - Structured card into two distinct flex regions:
     - `card-main-content` (`flex-1 min-h-0 flex flex-col`): Houses the header (house title, tenant counts, badges) and `.tenants-overview-section`. Contains zero warning markup.
     - `card-bottom-zone` (`mt-auto pt-2 flex flex-col flex-shrink-0`): Pinned to the bottom of the card. Contains `${missingWarningHtml}` directly above `${footerHtml}`.
   - Refined `card-warning-divider` styling (`mb-2` with self-contained amber strip) and `card-footer` styling (`pt-2.5 border-t border-slate-100 dark:border-slate-800`).
   - Replaced files and synchronized to `dist/win-x64/wwwroot/js/area-grid.js`.

2. **Automated Verification (`tests/web/components/tenant_file_integrity.test.js`)**:
   - Added assertions to verify:
     - `.card-bottom-zone .missing-docs-strip` is present when documents are missing.
     - `.card-main-content .missing-docs-strip` is null.
     - `.tenants-overview-section .missing-docs-strip` is null.
     - `.card-footer .missing-docs-strip` is null (not crammed into footer metrics).

## Test Results
- **Vitest**: 435 tests passing across 36 test files (100%).
- **.NET Unit Tests**: 926 tests passing in `HousingApplication.Tests` (100%).
