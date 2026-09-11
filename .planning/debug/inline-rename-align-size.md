---
status: resolved
trigger: "double clicking to rename moves the name bar to right side and becomes becomes. I don't want that. I want it to occupy the full space but I don't want it to move to the right side and become bigger. reduce the boldness of the rectangle while renmaing too. Its too bold. almost uncharasteric. make it blend with the rest of the app."
created: 2026-09-11
updated: 2026-09-11
---

## Symptoms
- **Expected**: When double-clicking to rename, the inline rename input should occupy the full horizontal space (`w-full flex-1 min-w-0`), but should NOT move to the right side (should remain left-aligned matching the row's document title), and should NOT become bigger/taller than the row (should remain compact with `text-xs py-0.5`). The rectangle/border should be subtle (`border-slate-300` with soft focus ring) so it blends seamlessly with the rest of the app instead of looking like a bold uncharacteristic blue rectangle.
- **Actual**: Double-clicking to rename caused the input text to jump to the right side (due to `dir="auto"` on Arabic document titles), caused the input to become bigger (~36px height with `text-sm py-1.5 border-2 shadow-sm rounded-lg`), and had an intensely bold saturated border (`border-blue-500` / `border-2`).
- **Errors**: No runtime errors; UI/UX alignment, sizing, and styling defect.
- **Timeline**: Introduced during recent quick task QCK-05 enlargement.
- **Reproduction**: Double-click any document name in Categories view or Timeline view.

## Root Causes
1. **Right-Side Shift (`dir="auto"`)**:
   - The `<input>` element was rendered with `dir="auto"`.
   - Because document titles start with Arabic characters (e.g., `عقد إيجار`), `dir="auto"` instructed the browser to switch the input direction to RTL (`direction: rtl; text-align: right`), causing the text, caret, and cursor to shift completely over to the right edge of the input.
   - The unedited document title in the dashboard sits in an LTR container and starts on the left side (after the checkbox and document icon). When double-clicked, the text appeared to jump across the screen to the right side.
2. **Vertical Bloat / Becoming Bigger**:
   - The input had classes `px-3 py-1.5 text-sm font-medium border-2 shadow-sm rounded-lg`.
   - `text-sm` (14px font, 20px line-height) plus `py-1.5` (12px vertical padding) and `border-2` (4px border) created an element of ~36px height.
   - The standard document row is sized around `text-xs` (12px font, 16px line-height), so the 36px input visibly expanded the row vertically, disrupting list compactness.
3. **Overly Bold Rectangle**:
   - The input used `border-blue-500` and `focus:ring-blue-500`, which created a stark, loud blue border that clashed with the soft slate palette of the surrounding card rows and badges (`border-slate-300` and `border-slate-200`).
4. **Full Space Requirement**:
   - The input and its container span/h4 already possessed `w-full` and `flex-1 min-w-0`, which correctly allows it to span the full available horizontal space in the flex row rather than shrink-wrapping short filenames.

## Resolution
1. **Removed `dir="auto"` to Prevent Right-Side Jumping**:
   - In `src/api/static/js/categories-view.js` and `src/api/static/js/timeline-view.js`, removed `dir="auto"` from the `<input>` element.
   - The input now retains standard left-aligned orientation matching the surrounding UI and document row.
2. **Compact Input Sizing**:
   - Replaced `px-3 py-1.5 text-sm font-medium border-2 border-blue-500 rounded-lg` with `px-2 py-0.5 text-xs font-normal rounded-md`.
   - This matches the `text-xs` font size and compact height (~22-24px) of the document row so it no longer stretches or becomes bigger than the row.
3. **Soft, Blended Border**:
   - Replaced loud `border-blue-500 focus:ring-blue-500` with subtle `border border-slate-300 rounded-md bg-white text-slate-800 focus:outline-hidden focus:border-blue-400 focus:ring-1 focus:ring-blue-400/30`.
   - The rectangle now blends harmoniously with the rest of the application's clean slate styling.
4. **Preserved Full Horizontal Width**:
   - Maintained `w-full min-w-0` on the `<input>` and `flex-1 min-w-0` on `titleSpan` and `titleH4`, allowing the rename bar to comfortably occupy all available width across the row.
5. **Asset Synchronization**:
   - Synchronized `src/api/static/js/categories-view.js` and `src/api/static/js/timeline-view.js` to `web-net/wwwroot/js/categories-view.js` and `web-net/wwwroot/js/timeline-view.js` (`diff -r` returns 0).
6. **Testing**:
   - Updated assertions in `tests/frontend/components/inline_rename.test.js` to verify `text-xs`, `px-2`, `py-0.5`, `w-full`, `min-w-0`, `border-slate-300`, and `getAttribute('dir') === null`.
   - Verified 143/143 Vitest frontend tests, 84/84 .NET xUnit tests, 30/30 Pytest backend tests, and Playwright E2E tests pass cleanly.
