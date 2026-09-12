# Quick Plan: Touch Press-and-Hold Drag-and-Drop Document Move Support on Tablets

## User Requirement
"pressing and holding the title on tab using fingers doesn't enable the move like it does on pc. add that support. make tests update docs and commit and push."

Implement touch-based drag-and-drop document move on tablets and touchscreens:
1. Long-press (press and hold ~280ms) on a document title or row enters touch drag mode with haptic feedback.
2. Floating drag avatar (`#touch-drag-avatar`) tracks the finger across the viewport without scrolling the page.
3. Hovering over a destination category folder dynamically highlights the card (`drag-over-active`).
4. Releasing finger over the destination folder triggers document move (`handleCategoryDrop` + `moveDocInDom` + toast notification).
5. Clean suppression of synthetic click on drop to prevent accidental document opening.
6. Short taps (< 280ms) and scrolling swipes (> 8px movement before timer) continue to work normally without delay or interference.
7. Multi-stack synchronization across `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/`.
8. Automated unit tests verifying touch drag lifecycle, cancel on scroll, drop dispatch, and click suppression.

## Affected Files
- `src/api/static/js/categories-view.js`
- `src/api/static/js/timeline-view.js`
- `src/api/static/js/doc-manager.js`
- `src/api/static/css/styles.css`
- `web-net/wwwroot/js/categories-view.js`
- `web-net/wwwroot/js/timeline-view.js`
- `web-net/wwwroot/js/doc-manager.js`
- `web-net/wwwroot/css/styles.css`
- `dist/win-x64/wwwroot/js/categories-view.js`
- `dist/win-x64/wwwroot/js/timeline-view.js`
- `dist/win-x64/wwwroot/js/doc-manager.js`
- `dist/win-x64/wwwroot/css/styles.css`
- `tests/frontend/components/touch_and_mobile_interactions.test.js`
- `.planning/STATE.md`

## Tasks

### Task 1: Implement Touch Drag Controller in `categories-view.js` & `styles.css`
- Add touch drag detection (`touchstart`, `touchmove`, `touchend`, `touchcancel`) on document rows and titles.
- Implement long-press hold timer (280ms), scroll-detection cancel threshold (8px), and haptic vibration (`navigator.vibrate`).
- Create floating `#touch-drag-avatar` element and highlight hover target via `document.elementFromPoint`.
- Execute move on valid target release via `handleCategoryDrop`, and suppress synthetic click via `_justFinishedTouchDrag`.
- Add dark/light CSS styling for `#touch-drag-avatar`.

### Task 2: Synchronize Changes Across All Three Web Roots
- Mirror changes to `web-net/wwwroot/` and `dist/win-x64/wwwroot/`.
- Ensure 0 diff across mirrors.

### Task 3: Add Automated Unit Tests & Verification
- Add comprehensive unit tests in `touch_and_mobile_interactions.test.js` verifying the touch drag lifecycle.
- Run full test suites (Vitest, .NET xUnit).
- Update `.planning/STATE.md` and create `SUMMARY.md`.
- Commit and push to `origin/main`.
