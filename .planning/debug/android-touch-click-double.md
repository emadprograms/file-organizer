---
status: resolved
trigger: "when viewing on my android tab. often a single click will be registered as double click. add support for mobile devices and touchscreens as well. I'm refering to the double click when clicking on a file. I press to open the file. it registers double click and opens the rename dialog"
created: 2026-09-12
updated: 2026-09-12
---

## Current Focus
- hypothesis: On Android tablets and touchscreen devices, tapping a document card/title synthesizes rapid touch/mouse events or triggers browser double-tap detection (`event.detail >= 2` or `dblclick`). Because `titleSpan.ondblclick` and `titleH4.ondblclick` listen unconditionally for `dblclick`, the browser triggers inline rename instead of opening the document. Furthermore, absence of `touch-action: manipulation` and hidden 3-dots menu buttons on touch devices degrade the mobile experience.
- test: Simulate touch interactions on document rows and titles in Categories View and Timeline View. Verify that tapping on touch/mobile devices opens the document and NEVER triggers inline rename. Verify that double-click inline rename only functions with desktop mouse pointers or explicit 3-dot menu actions.
- expecting: Touching or tapping a file on mobile/touchscreen devices opens the document cleanly. Inline rename is never triggered by touch taps. 3-dots menu button is visible on touchscreens. CSS touch-action is optimized.
- resolution: Implemented `isTouchEvent(e)` and `isTouchOrMobileDevice()` with global touch/pointer tracking (`touchstart`, `pointerdown`). Guarded `handleInlineRename` and `ondblclick` handlers in both `categories-view.js` and `timeline-view.js` so touch interactions open the file and never enter rename mode. Debounced category card and document row click handlers against touch bounce. Added `touch-action: manipulation`, `-webkit-overflow-scrolling: touch`, touchscreen 3-dot menu visibility (`opacity: 1 !important`), touch target sizing, and input zoom protection in `styles.css`.

## Symptoms
- **Expected**: Pressing or tapping a document on an Android tablet or touchscreen device should open the document in the viewer without triggering inline rename.
- **Actual**: Pressing a file on an Android tablet often registers as a double click, which immediately opens the inline rename input dialog and summons the on-screen keyboard instead of opening the file.
- **Reproduction**:
  1. Open the file organizer on an Android tablet or touch-enabled browser.
  2. Tap on any document in the Categories or Timeline view.
  3. Instead of viewing the PDF, an inline text input appears to rename the file.

## Root Causes
1. **Unconditional `ondblclick` on Document Titles**:
   `categories-view.js` and `timeline-view.js` attached `ondblclick` directly to the title element (`doc-title-text`), which occupies most of the clickable card width.
2. **Touch-to-Mouse Event Synthesis on Android/Touchscreens**:
   Capacitive screen contact and Android Chrome touch-to-mouse emulation often fire rapid click events or trigger double-tap gestures (`e.detail >= 2`), causing the browser to dispatch a `dblclick` event.
3. **Double-Click Metaphor Mismatch on Touch Devices**:
   Touchscreens do not have a double-click gesture. Tapping a file on mobile should open it. Document renaming on mobile/touch is handled explicitly via the 3-dots dropdown menu ("Rename Document").
4. **Missing `touch-action: manipulation`**:
   Without `touch-action: manipulation`, mobile browsers maintain a 300ms double-tap gesture tracking window, causing tap delays and false double-tap detections.
5. **Hover-Only 3-Dots Menu Button**:
   `.doc-menu-btn` had `opacity-0 group-hover:opacity-100`, which hides the 3-dots action menu on touchscreens where hover does not exist.

## Resolution
1. **Touch Interaction Detection & Guards**:
   - Implemented `isTouchEvent(e)` checking `e.pointerType` ('touch'/'pen'), global window touch tracking (`window._lastTouchTimestamp < 1500`), coarse pointer media queries, and mobile user agents.
   - In `categories-view.js` and `timeline-view.js`, `titleSpan.ondblclick` and `titleH4.ondblclick` intercept touch events and call `openDocument(doc.vault_id, currentTitle, doc.category)`, completely bypassing inline rename.
   - Guarded `handleInlineRename(e, ...)` so any touch event passed into it redirects to `openDocument`. Programmatic renaming via 3-dots menu (`e = null`) continues to work on touch and desktop.
   - Desktop mouse double-clicking remains 100% functional.
2. **Touch Debounce & Idempotency**:
   - Added 250ms touch-event debounce to category folder accordion cards (`card.onclick`) to prevent touch screen bounce from toggling open and immediately closed.
   - Added 250ms debounce to document row clicks and 350ms idempotency guard in `openDocument` (`doc-viewer.js`) to prevent duplicate PDF worker tearing down and restarts.
3. **Touchscreen CSS Support (`styles.css`)**:
   - `touch-action: manipulation` on `html, body, button, a, input, select, textarea, .cursor-pointer, .category-folder-card, .category-doc-item, .house-card, .doc-title-text`.
   - `-webkit-tap-highlight-color: transparent`.
   - Smooth momentum scrolling: `-webkit-overflow-scrolling: touch`.
   - `@media (hover: none), (pointer: coarse)`:
     - `.doc-menu-btn` set to `opacity: 1 !important` (permanently visible on touchscreens).
     - Touch targets increased to min 32px height.
     - `.doc-title-text` has `user-select: none; cursor: pointer !important` to prevent Android Chrome text selection engine from simulating double-click.
     - `.inline-rename-input` font size adjusted to 14px to prevent unwanted mobile browser auto-zooming.
4. **Parity & Verification**:
   - Synchronized static assets across `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/` with zero diff.
   - Created 10 automated unit tests in `tests/frontend/components/touch_and_mobile_interactions.test.js`.
   - All 24 Vitest test files (219 tests) passed (100%).
   - All 146 .NET xUnit tests passed (100%).
   - All 31 Python backend pytest tests passed (100%).

