---
status: resolved
trigger: "on my tab. when the tenant documents are open. j often cannot scroll to the bottom to see the last document. (not sure if this happens on my court but it suits happen on my tab)"
created: 2026-09-15
updated: 2026-09-15
---

## Current Focus
- hypothesis: On tablet/touchscreen devices, three compounding factors prevent scrolling to the bottom of tenant documents: (1) h-screen (100vh) extends 40-80px beneath tablet browser dynamic toolbars; (2) nested overflow-y-auto with overscroll-behavior-y: contain on both #document-list-panel and #document-list without flex-1 min-h-0 traps touch scrolling gestures; and (3) #document-list has only p-3 (12px) bottom padding with no safe-area buffer, so the last document is cut off by the viewport edge or floating batch bar.
- test: Inspect container styling and overflow hierarchy. Verify in browser/DOM tests that #document-list-panel is overflow-hidden, #document-list is flex-1 min-h-0 overflow-y-auto with generous bottom padding (pb-28), and viewport height respects dynamic viewport (100dvh).
- expecting: On tablets and desktops alike, opening tenant documents allows smooth scrolling all the way to the bottom with the last document fully visible and clickable above the viewport edge.
- resolution: Set #document-list-panel to overflow-hidden so segmented tabs remain pinned at top. Set #document-list to flex-1 min-h-0 overflow-y-auto with generous bottom clearance (pb-28 sm:pb-32 and max(8rem, env(safe-area-inset-bottom, 3rem)) on tablets/touchscreens). Sized viewport with 100dvh to eliminate mobile toolbar cut-off. Verified by 18 touch/mobile unit tests, 438 Vitest tests, and 926 .NET unit tests.

## Symptoms
- **Expected**: When viewing tenant documents (in Categories or Timeline view) on a tablet or desktop, the user should be able to scroll all the way to the bottom to clearly see and interact with the last document in the list.
- **Actual**: On tablet ("tab"), when tenant documents are open, the user often cannot scroll to the bottom to see the last document (it gets cut off or cannot be scrolled into view).
- **Reproduction**: Open a house and tenant with multiple documents on a tablet or touch-enabled browser, scroll down to the bottom of the list.

## Root Causes
1. **100vh Viewport Overflow on Tablets (`h-screen`)**:
   `index.html` uses `h-screen` (`100vh`) on the main container. On mobile/tablet browsers (Android Chrome, iPad Safari), `100vh` calculates height based on the screen without toolbars, pushing the bottom 40-80px of the page below the visible viewport.
2. **Nested Conflicting Scroll Containers & Touch Trapping**:
   `#document-list-panel` had `overflow-y-auto` AND `#document-list` had `overflow-y-auto`, but `#document-list` lacked `flex-1 min-h-0`. Combined with `overscroll-behavior-y: contain` in `styles.css`, touch gestures on the inner container become trapped or fail to bubble, while the top tabs bar improperly scrolled away.
3. **Insufficient Bottom Padding & Safe Area Inset**:
   `#document-list` only had `p-3` (12px) padding, with no bottom clearance for tablet home indicators, browser gesture bars, or the floating `#batch-action-bar`.

## Resolution
1. Change `#document-list-panel` to `overflow-hidden flex flex-col`, keeping segmented tabs permanently pinned at the top.
2. Give `#document-list` `flex-1 min-h-0 overflow-y-auto` and generous bottom padding (`pb-28` / `padding-bottom: max(6rem, env(safe-area-inset-bottom, 2rem))`).
3. Add `h-[100dvh]` support to the main container and body in `index.html` and `styles.css` so mobile/tablet browser toolbars do not push the bottom of the container off-screen.
4. Remove redundant `overflow-y-auto` from `#document-list-panel` in `styles.css`.
