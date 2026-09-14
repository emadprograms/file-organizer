---
status: resolved
trigger: "the sidebar isn't adjustable in the tab. the tenant sidebar."
created: 2026-09-14
updated: 2026-09-14
---

## Current Focus
- hypothesis: The resizer divider bar (`resizer-2` for the tenant/document list panel, as well as `resizer-1` for the main sidebar) only listens to mouse events (`mousedown`, `mousemove`, `mouseup`) and lacks touch event handlers (`touchstart`, `touchmove`, `touchend`, or Pointer Events). Consequently, on tablet devices (Android Tab, iPad, touchscreen), dragging the resizer has no effect and cannot adjust sidebar width.
- test: Inspect `resizer.js` and verify whether touch/pointer drag events are implemented. Test touch interaction simulation on resizer handles.
- expecting: Touch dragging should update panel widths smoothly on tablet/touch devices just like mouse drag on desktop.
- next_action: debug complete

## Symptoms
- **Expected behavior**: Dragging the vertical border/resizer bar should smoothly adjust the width of the tenant sidebar on tablet devices.
- **Actual behavior**: On a tablet device (touchscreen / iPad / Android Tab), dragging the resizer bar has no effect at all.
- **Error messages**: None reported.
- **Timeline**: Not sure / never supported.
- **Reproduction**:
  1. Open the application on a tablet (or browser emulating touch events).
  2. Navigate to a house to show the tenant sidebar (`document-list-panel`).
  3. Attempt to drag the vertical resizer divider bar (`resizer-2` or `resizer-1`) with a finger or stylus.
  4. The sidebar width does not change.

## Investigation Evidence
1. In `src/HousingApplication.Web/wwwroot/js/resizer.js`:
   - `setupResizer` only attached event listeners for `resizer.addEventListener('mousedown')`, `document.addEventListener('mousemove')`, and `document.addEventListener('mouseup')`.
   - No listeners existed for `touchstart`, `touchmove`, `touchend`, `touchcancel`, or Pointer Events (`pointerdown`, `pointermove`, `pointerup`, `pointercancel`).
   - On touchscreens/tablets (Android Galaxy Tab, iPad, touchscreen laptops), finger/stylus drags dispatch TouchEvents (`touchstart`, `touchmove`, `touchend`). Because `mousemove` is not fired during touch drags and no touch handlers existed, dragging the resizer handle produced zero response.
2. In `src/HousingApplication.Web/wwwroot/index.html` & `styles.css`:
   - `#resizer-2` had class `w-1` (only 4px wide). On high-DPI tablet screens, a 4px target is too narrow for a finger tap/drag.
   - `touch-action: none` was missing from the resizer handles in CSS, causing browsers to treat drag attempts as native scroll/pan gestures instead of triggering resizer logic.
   - Persistence in `resizer.js` was hardcoded to only persist `main-sidebar` (`localStorage.getItem('sidebar_width')`), ignoring the tenant sidebar (`document-list-panel`).

## Root Cause
1. `resizer.js` lacked touch event listeners (`touchstart`, `touchmove`, `touchend`, `touchcancel`) and Pointer Event listeners (`pointerdown`, `pointermove`, `pointerup`, `pointercancel`), relying exclusively on mouse events (`mousedown`, `mousemove`, `mouseup`). On tablet devices, touch interactions trigger touchmove/touchend rather than continuous mousemove events.
2. Missing `touch-action: none` on `#resizer-1` and `#resizer-2` in CSS allowed the tablet browser's default touch scrolling and pan gestures to intercept horizontal drag gestures.
3. The 4px physical width (`w-1`) lacked an expanded hit target, making finger targeting difficult on high-resolution touchscreens.
4. Tenant sidebar (`document-list-panel`) width settings were not persisted to `localStorage` (only `main-sidebar` was persisted).

## Solution / Fix Applied
1. **`src/HousingApplication.Web/wwwroot/js/resizer.js`** (and mirrored in `dist/win-x64/wwwroot/js/resizer.js`):
   - Added Touch Event listeners: `touchstart` (with active touch ID tracking and `{ passive: false }`), `touchmove` (calculating delta from touch clientX and updating panel width), `touchend`, and `touchcancel`.
   - Added Pointer Event listeners (`pointerdown`, `pointermove`, `pointerup`, `pointercancel`) with `setPointerCapture` where supported.
   - Added dynamic panel width storage persistence (`localStorage.setItem(storageKey, panel.style.width)` and restoration on setup) supporting both `sidebar_width` and `document_list_panel_width`.
   - Added `is-resizing` CSS class during active drags for responsive visual feedback.
2. **`src/HousingApplication.Web/wwwroot/css/styles.css`** (and mirrored in `dist/win-x64/wwwroot/css/styles.css`):
   - Applied `touch-action: none; position: relative; user-select: none;` to `#resizer-1` and `#resizer-2`.
   - Added `::before` pseudo-element with 20px extra hit target (`left: -10px; right: -10px; z-index: 25;`) for effortless finger/stylus grabbing on tablets.
   - Added active/resizing blue highlight state (`#resizer-1.is-resizing, #resizer-2.is-resizing, :active { background-color: #3b82f6 !important; }`).
3. **`src/HousingApplication.Web/wwwroot/index.html`** (and mirrored in `dist/win-x64/wwwroot/index.html`):
   - Added `dark:bg-slate-800` to `#resizer-2` to match `#resizer-1` in dark mode.
4. **`tests/web/components/resizer.test.js`**:
   - Created comprehensive Vitest tests verifying tablet touch drag, percentage clamping (20%–60%), touchcancel termination, main sidebar touch drag, persistence & restoration in localStorage, mouse compatibility, and CSS touch-action rules.

## Verification
- Ran full test suite (`npm test`): 35 test files passed (408 tests passed, 0 failures).
- Verified `tests/web/components/resizer.test.js` (7 new tests all passing).
- Verified `tests/web/components/sidebar.test.js` (10 tests all passing).
- Verified `tests/web/components/touch_and_mobile_interactions.test.js` (16 tests all passing).


