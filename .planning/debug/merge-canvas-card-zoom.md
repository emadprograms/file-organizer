---
status: resolved
trigger: "when there is so much space on the canvas, why are the cards so small? the user should be able to adjust the the size of the cards with a plus and minus button in the header or by ctrl + or ctrl scroll."
created: 2026-09-18
updated: 2026-09-18
slug: merge-canvas-card-zoom
---

# Debug & Feature Enhancement: Canvas Card Sizing & Zoom Controls (+/- Buttons, Ctrl+, Ctrl+Scroll)

## Root Cause
1. **Rigid Grid Classes**: `#merge-preview-cards` and `#merge-docs-list` used rigid Tailwind `grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5`. On displays >= 1024px, the grid created 5 rigid ~180px columns. In a 2-doc merge, Card 1 took col 1, inline swap took col 2, Card 2 took col 3, and cols 4 and 5 were completely blank while cards were tiny.
2. **Fixed Card Dimensions**: Card thumbnails had fixed small heights and widths without scaling support.
3. **Missing Zoom Controls**: Headers lacked interactive zoom buttons, keyboard event handlers (`Ctrl +`, `Ctrl -`, `Ctrl 0`), and mouse wheel zooming (`Ctrl + Scroll`).

## Solution Implemented
1. **Dynamic CSS Variables & Dynamic 2-Doc Flex**:
   - Added `--merge-card-min-width`, `--merge-thumb-height`, `--merge-card-max-width`, `--editor-card-min-width`, `--editor-thumb-height` in `styles.css`.
   - Added `.merge-flex-2doc` (`flex flex-wrap items-center justify-center gap-4 sm:gap-6 pb-4`), allowing 2 cards to take up ~430px each (up to 520px max) with centered inline swap button.
   - Added `.merge-grid-dynamic` and `.editor-grid-dynamic` for responsive `repeat(auto-fit, minmax(...))` multi-doc layouts.
2. **Zoom Controls Group**:
   - Added `btn-merge-zoom-out`, `btn-merge-zoom-reset`, `merge-zoom-level-label`, and `btn-merge-zoom-in` in `#merge-docs-modal` header.
   - Added `btn-editor-zoom-out`, `btn-editor-zoom-reset`, `editor-zoom-level-label`, and `btn-editor-zoom-in` in `#doc-page-editor-modal` header.
3. **Granular 7-Step Scaling**:
   - Supported scale levels: `70%`, `85%`, `100%`, `120%`, `145%`, `175%`, `210%`.
   - `localStorage` persistence across sessions.
4. **Universal Event Handlers**:
   - Mouse wheel (`Ctrl + Scroll`): Wheel up zooms in, wheel down zooms out with `e.preventDefault()`.
   - Keyboard shortcuts (`Ctrl +`, `Ctrl =`, `Ctrl -`, `Ctrl 0`).
   - Clean handler deduplication on `window` and `document` preventing duplicate triggers across environments.
5. **High-Resolution PDF Rendering**:
   - Increased preview thumbnail resolution to 360×480 in 2-doc preview cards and 320×420 in reorder rows.

## Verification
- Unit test suite: `tests/web/components/merge_documents.test.js` (22/22 passed).
- Unit test suite: `tests/web/components/doc_page_editor.test.js` (24/24 passed).
- Full application suite: All 42 test files and 610 tests passed (100% pass rate).
- Web assets synchronized across `src/` and `dist/win-x64/wwwroot/`.
