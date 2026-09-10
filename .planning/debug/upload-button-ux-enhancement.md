# UX Enhancement: Upload Button Redesign & Drag-and-Drop Hint

**Date:** 2026-09-10  
**Context:** User feedback on Ingest action button terminology, placement, icon duplication, and hover responsiveness.

## User Feedback Addressed
1. **Terminology:** Changed "Ingest" to **"Upload"** across the navbar trigger, dialog headers, progress indicators, and toast notifications.
2. **Double-plus Bug:** Eliminated duplicate plus icon (previously rendered as `+ + Ingest` due to both SVG plus and literal `+` text). The button now renders a single crisp SVG plus icon alongside `Upload` and keyboard shortcut badge `⌘I`.
3. **Navbar Placement & Visual Hierarchy:**
   - Standard modern layout: Search bar on the left (`#btn-search-trigger`), then a subtle drag-and-drop hint pill (`#btn-drag-hint`), followed by the primary CTA Upload button on the far right (`#btn-ingest-trigger`).
4. **Tactile Hover Animation:**
   - Added smooth scaling (`hover:scale-105`), active press (`active:scale-95`), color shift from `bg-blue-600` to `hover:bg-blue-500`, glowing soft shadow (`hover:shadow-blue-500/25`), and a smooth 90° rotation on the plus icon on hover (`group-hover:rotate-90`).
5. **Drag-and-Drop Hint Pill:**
   - Placed an interactive hint pill to the left of the Upload button: `[ 📄 or drop PDF anywhere ]`.
   - Styled with dashed borders and hover states; clicking the pill also opens the Upload dialog.

## Verification & Parity
- **Vitest Frontend Tests:** 68 passing (100%).
- **Playwright Browser Tests:** 8 passing (100%).
- **Pytest Backend Tests:** 29 passing (100%).
- **.NET xUnit Tests:** 43 passing (100%).
- **Monorepo Parity:** `src/api/static/` and `web-net/wwwroot/` 100% identical (`diff -r` returned 0 diffs).
