---
status: resolved
trigger: "don't write the text move when dragging around. what is the cloud icon before the title even supposed to mean? change that to something else too?"
created_at: 2026-09-12T11:15:00.000Z
resolved_at: 2026-09-12T11:16:00.000Z
---

# Debug: Touch Drag Avatar Visual Polish (Remove Move Text & Replace Cloud Icon)

## Symptoms
1. When dragging a document with touch/finger on a tablet, the floating avatar displayed a badge with the text `نقل • Move`.
2. The icon preceding the document title was a cloud upload icon (`d="M7 16a4 4 0 01-.88-7.903..."`), which did not represent moving an existing document.

## Root Cause
In `startTouchDrag()` inside `src/api/static/js/categories-view.js`, the avatar HTML template included:
- A cloud upload SVG icon.
- A trailing badge `<span class="... font-bold flex-shrink-0">نقل • Move</span>`.

## Resolution
1. **Removed Move Text Badge:** Deleted the `نقل • Move` text badge element from `#touch-drag-avatar`.
2. **Replaced Icon:** Replaced the cloud upload SVG with the clean, standard document/file outline SVG used across the app (`d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"`).
3. **Synchronized:** Mirrored updated `categories-view.js` to `web-net/wwwroot/js/` and `dist/win-x64/wwwroot/js/` with zero diff.
4. **Updated Tests:** Updated unit test expectations in `tests/frontend/components/touch_and_mobile_interactions.test.js` to verify `avatar.textContent` does not contain `Move` and verifies the document SVG icon is present.

## Verification
- All 232 Vitest tests passed across 24 test files (100%).
- All 146 .NET xUnit tests passed (100%).
