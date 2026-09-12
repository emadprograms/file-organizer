# Quick Plan: Add Dark Mode Support on the App

## User Requirement
"add dark mode support on the app as well."

Implement comprehensive dark mode across the entire application with:
1. Tailwind `darkMode: 'class'` configuration and FOUC prevention script in `<head>`.
2. Dedicated `theme-manager.js` component with `toggleTheme()`, `setTheme()`, `getTheme()`, and `localStorage` persistence.
3. Interactive theme toggle button in the top navbar (`#btn-theme-toggle`) with Sun/Moon dynamic icons.
4. Keyboard shortcut (`Shift+D`) and Command Palette command integration.
5. Dark theme styling rules in `styles.css` and template classes across all views (Area Grid, House Profile, Categories, Timeline, Live Peek, Modals, Batch Action Bar).
6. 100% static asset parity across `web-net/wwwroot/`, `src/api/static/`, and `dist/win-x64/wwwroot/`.
7. Comprehensive frontend unit test suite in `tests/frontend/components/theme_manager.test.js`.

## Affected Files
- `web-net/wwwroot/index.html`
- `web-net/wwwroot/css/styles.css`
- `web-net/wwwroot/js/theme-manager.js` (new)
- `web-net/wwwroot/js/keyboard-shortcuts.js`
- `web-net/wwwroot/js/command-palette.js`
- `web-net/wwwroot/js/app.js`
- `src/api/static/index.html`
- `src/api/static/css/styles.css`
- `src/api/static/js/theme-manager.js` (new)
- `src/api/static/js/keyboard-shortcuts.js`
- `src/api/static/js/command-palette.js`
- `src/api/static/js/app.js`
- `dist/win-x64/wwwroot/index.html`
- `dist/win-x64/wwwroot/css/styles.css`
- `dist/win-x64/wwwroot/js/theme-manager.js` (new)
- `dist/win-x64/wwwroot/js/keyboard-shortcuts.js`
- `dist/win-x64/wwwroot/js/command-palette.js`
- `dist/win-x64/wwwroot/js/app.js`
- `tests/frontend/components/theme_manager.test.js` (new)

## Tasks

### Task 1: Create `theme-manager.js`, Configure Tailwind Dark Mode & Navbar Toggle
- Configure Tailwind `darkMode: 'class'` in `index.html`.
- Add pre-hydration theme detection script in `<head>` to prevent FOUC.
- Add `#btn-theme-toggle` in `#top-navbar` alongside shortcuts trigger.
- Implement `web-net/wwwroot/js/theme-manager.js` with toggle, storage, system preference sync, and `Shift+D` shortcut.
- Integrate toggle into `command-palette.js` and `keyboard-shortcuts.js`.

### Task 2: Polish Dark Theme CSS Styling Across Views & Modals
- Add comprehensive dark mode rules in `styles.css` covering scrollbars, selected cards, modals, tables, badges, and view panels.
- Ensure smooth transitions and cohesive slate-900 / slate-950 dark aesthetic matching the sidebar.

### Task 3: Add Frontend Unit Tests & Multi-Stack Verification
- Create `tests/frontend/components/theme_manager.test.js` testing initialization, toggle, persistence, button state, and shortcuts.
- Verify full test suite passes (Vitest, .NET xUnit, Pytest).
- Ensure 0 diff across static mirrors.
