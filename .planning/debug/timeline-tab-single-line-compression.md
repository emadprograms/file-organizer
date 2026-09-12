---
status: resolved
trigger: "make sure that tenant timeline and housing timeline stay in one line only. if the user compresses it then the text should start disappearing but not move to the next line."
created_at: 2026-09-12T13:35:00.000Z
resolved_at: 2026-09-12T13:38:00.000Z
---

# Debug: Tenant Timeline and House Timeline Single-Line Non-Wrapping Truncation

## Symptoms
1. When viewing a house or a tenant, the timeline tab label displays "House Timeline" or "Tenant Timeline".
2. When the user compresses or narrows the left document panel (or on narrower viewports/tablets), multi-word tab labels wrapped onto a second line (e.g. "Tenant" on line 1, "Timeline" on line 2), ballooning the tab bar height and distorting the segmented tabs layout.

## Root Cause
1. In `src/api/static/index.html`, the segmented tab button elements (`#tab-categories`, `#tab-timeline`) and their label spans (`#tab-categories-label`, `#tab-timeline-label`) did not have `whitespace-nowrap`, `overflow-hidden`, and `min-w-0` applied.
2. In `app.js` and `router.js`, tab activation toggled `className` using hardcoded class strings that lacked `min-w-0`, `overflow-hidden`, and `whitespace-nowrap`.
3. Flex child items defaulted to `min-width: auto`, preventing the buttons and labels from gracefully shrinking below their intrinsic text width and triggering CSS text truncation/clipping.

## Resolution
1. **Single-Line Non-Wrapping Markup:** Updated `index.html` tab buttons with `flex-1 min-w-0 py-1.5 px-2.5 ... overflow-hidden whitespace-nowrap` and label spans with `truncate whitespace-nowrap min-w-0`. Tab container received `min-w-0`.
2. **Explicit CSS Enforcement:** Added rules in `styles.css` for `#tab-categories`, `#tab-timeline`, `#tab-categories-label`, and `#tab-timeline-label` with `white-space: nowrap !important;`, `overflow: hidden !important;`, `text-overflow: ellipsis !important;`, and `min-width: 0 !important;` to guarantee text remains on one line and disappears/truncates cleanly upon panel compression.
3. **Dynamic State Synchronization:** Updated `app.js` and `router.js` tab switching classNames to preserve `min-w-0`, `overflow-hidden`, and `whitespace-nowrap`. Added `title` attribute synchronization on tab labels so users can hover for full text when truncated.
4. **Mirroring:** Synchronized all updated files across `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/` with verified zero diff.
5. **Unit Tests:** Added tests in `tests/frontend/components/tab_labels.test.js` validating title tooltip assignment, compression resilience classes, and CSS nowrap & truncation rules.

## Verification
- All 257 Vitest tests passed across 25 test files (100%).
- All 146 .NET xUnit tests passed (100%).
- Zero diff verified across all 3 static web trees.
