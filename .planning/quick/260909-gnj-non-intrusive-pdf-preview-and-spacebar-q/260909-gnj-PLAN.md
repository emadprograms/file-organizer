# Quick Task: Non-Intrusive PDF Preview & macOS-Style Spacebar Quick Look

## Description
Refactor the PDF preview interaction model to solve the intrusive hover behavior, iframe mouse traps, and 3-dot menu blocking, while introducing a native macOS-style Spacebar "Quick Look" modal:
1. **Polite, Non-Intrusive Hovercard**:
   - Scope hover trigger exclusively to document preview icons/badges (not the entire row).
   - Set `pointer-events: none` on the floating preview tooltip so it never blocks clicks or traps the cursor inside iframes.
   - Anchor the tooltip relative to the target element (no cursor chasing).
   - Increase trigger delay to 450ms; dismiss immediately on scroll, click, or `Escape`.
   - Explicitly hide and suppress preview whenever the cursor hovers anywhere near the 3-dot action menu.
2. **macOS-Style Spacebar Quick Look Modal**:
   - Track currently active/selected document on click or focus.
   - Pressing `Space` toggles a clean, responsive Quick Look modal with full PDF rendering and metadata header.
   - Pressing `Space` or `Esc` closes the Quick Look modal.
   - Include a dedicated Quick Look / Peek action button on each document card for mouse users.

## Tasks
1. **Refactor Hover Preview Engine (`src/api/static/js/pdf-preview.js`, `src/api/static/css/styles.css`)**
   - Ensure `#pdf-preview-tooltip` always has `pointer-events: none` so it never intercepts mouse events or captures the pointer inside the iframe.
   - Remove cursor-following `mousemove` logic; anchor tooltip to target element with viewport boundary clamping.
   - Increase hover delay to 450ms.
   - Add instant dismiss triggers: `window.addEventListener('scroll')`, `document.addEventListener('mousedown')`, and `document.addEventListener('keydown')` (Esc).
   - Export `showPreviewAnchor(targetEl, vaultId, title)` and explicit suppression helpers.

2. **Implement macOS-Style Quick Look Modal (`src/api/static/index.html`, `src/api/static/js/pdf-preview.js`)**
   - Add a lightweight, centered Quick Look modal with backdrop, document title, tenant/category badges, iframe viewer, and keyboard hints (`Space` to close, `Esc` to close).
   - Implement `openQuickLook(vaultId, title, meta)` and `closeQuickLook()`.
   - Add a global `keydown` listener for `Space` (key code 'Space' / ' ') that checks if user is not in an input/textarea/select/modal, and toggles Quick Look for the selected document.

3. **Integrate Document Cards & Menus (`src/api/static/js/categories-view.js`, `src/api/static/js/timeline-view.js`)**
   - In Categories View and Timeline View, isolate the hover preview trigger to the document icon or a dedicated preview badge.
   - Add a Quick Look button or icon click handler.
   - Ensure the 3-dot menu button has mouseenter handlers that immediately cancel any pending or active preview tooltip.
   - Track `window.setSelectedDoc(doc, title)` when clicking or interacting with cards.

4. **Testing & Verification**
   - Verify that clicking the 3-dot menu is unobstructed and comfortable.
   - Verify hover preview only triggers on the designated preview target and never traps the mouse.
   - Verify pressing `Space` opens/closes Quick Look seamlessly.
   - Verify scrolling or pressing `Esc` dismisses previews immediately.
