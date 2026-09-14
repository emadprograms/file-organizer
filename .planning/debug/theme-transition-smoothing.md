---
status: resolved
trigger: "also the switch from light mode to dark mode and back is very jarring. its not smooth. is it possible to make it smooth. make it look like luxury. right now one element becomes dark first and then second and all. make these changes after you're done finishing your current changes."
created: 2026-09-14T14:09:00Z
updated: 2026-09-14T14:11:00Z
---

## Resolution Summary
- **Root Cause**:
  1. Main layout containers (`#main-sidebar`, `#top-navbar`, `#document-list-panel`, `#area-grid-panel`, `#document-empty-state`, `#database-inspector-panel`) had no CSS transition properties and repainted instantaneously in 0ms.
  2. `body` had `transition-colors duration-150` (150ms), cards had 150ms transitions, and various buttons had 200ms transitions.
  3. When toggling the theme, elements with 0ms transition flipped immediately, followed by the 150ms body/cards, followed by the 200ms buttons. This created a jarring, staggered repaint where elements changed color in waves.
- **Fix Applied**:
  1. **Synchronized Transition Mechanism**:
     - In `theme-manager.js`, added `enableThemeTransition()`. Whenever the user changes the theme (via button click, `Shift+D` shortcut, or `setTheme`), the class `.theme-transitioning` is applied to `document.documentElement` for exactly 350ms, then automatically removed.
     - Initial load (`initTheme`) passes `animate = false` to guarantee zero visual flash on boot.
  2. **Luxury Easing & Synchronized Properties**:
     - In `styles.css`, configured `html.theme-transitioning, html.theme-transitioning *` to transition `background-color`, `border-color`, `color`, `fill`, `stroke`, and `box-shadow` with `300ms cubic-bezier(0.4, 0, 0.2, 1) !important;` and `transition-delay: 0ms !important;`.
     - Added `@media (prefers-reduced-motion: reduce)` override to disable transitions when requested by accessibility preferences.
     - Removed mismatched `duration-150` from `<body class="...">` in `index.html` so transitions are unified through the master class.
  3. **Distribution Sync**:
     - Maintained 100% byte-for-byte parity across `src/HousingApplication.Web/wwwroot/` and `dist/win-x64/wwwroot/`.
  4. **Automated Regression Tests**:
     - Added 5 unit tests in `tests/web/components/theme_manager.test.js` validating transition class lifecycle, initial-load safety, duration token enforcement, and reduced-motion support.

## Verification
- `npm test`: 33 test files passed, 383 tests passed.
- `dotnet test`: 925 tests passed.
- Byte parity: `diff -r src/HousingApplication.Web/wwwroot/ dist/win-x64/wwwroot/` verified 100% identical.
