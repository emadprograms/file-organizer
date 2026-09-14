---
status: complete
task_id: 260914-soften-light-mode-whiteness
slug: soften-light-mode-whiteness
date: 2026-09-14
---

# Quick Task Summary: Soften Light Mode Whiteness for Eye Comfort

**Task ID**: `260914-soften-light-mode-whiteness`  
**Status**: Complete  
**Date**: 2026-09-14  

---

## 1. Overview
Addressed user feedback regarding excessive whiteness and screen glare in light mode ("reduce the whiteness in light mode.. like its too white. I don't want it that white. basically make it a bit greyer. the grey shouldn't be visible but the whitness should be reduced"):
- Calibrated `:root` semantic tokens for light-mode surfaces: lowered luminance of the base canvas, panels, cards, and borders to eliminate blinding glare while keeping surfaces looking clean and pristine.
- Introduced scoped `html:not(.dark)` eye-comfort rules targeting body, utility surfaces (`.bg-slate-50`, `.bg-slate-100`, `.bg-white`, `.bg-white/90`, `.bg-white/95`), and primary panels (`#top-navbar`, `#document-list-panel`, `#area-grid-panel`, `#database-inspector-panel`, `#document-viewer-panel`).
- Maintained crisp `#ffffff` on text input fields and active segmented tab controls (`#tab-categories.bg-white`, `#tab-timeline.bg-white`) for sharp readability and contrast.
- Ensured all existing dark mode rules remain strictly intact and unaffected.
- Ensured 100% byte-for-byte parity between `src/HousingApplication.Web/wwwroot/css/styles.css` and `dist/win-x64/wwwroot/css/styles.css`.
- Added comprehensive unit test suite in `tests/web/components/light_mode_eye_comfort.test.js`.

## 2. Changes Made
1. **`src/HousingApplication.Web/wwwroot/css/styles.css`**:
   - Updated `:root` tokens:
     - `--surface-canvas`: `#edf0f5`
     - `--surface-panel`: `#f6f8fb`
     - `--surface-card`: `#f9fafb`
     - `--surface-elevated`: `#ffffff`
     - `--surface-hover`: `#eef2f6`
     - `--border-subtle`: `#e2e8f0`
     - `--border-default`: `#cbd5e1`
     - `--border-emphasis`: `#94a3b8`
   - Added scoped `html:not(.dark)` section under `/* ── Light Mode Surface Calibration & Eye Comfort ─────────────────── */`:
     - `html:not(.dark) body`, `.bg-slate-50`, `#area-grid-panel`, `#database-inspector-panel`: `#edf0f5`
     - `html:not(.dark) .bg-slate-100`: `#e4e8ef`
     - `html:not(.dark) .bg-white`: `#f8fafc`
     - `html:not(.dark) .bg-white/90`: `rgba(248, 250, 252, 0.92)`
     - `html:not(.dark) .bg-white/95`: `rgba(248, 250, 252, 0.96)`
     - `html:not(.dark) #top-navbar`: `rgba(248, 250, 252, 0.92)` with border `#e2e8f0`
     - `html:not(.dark) #document-list-panel`: `#f5f7fa` with border `#e2e8f0`
     - `html:not(.dark) #document-viewer-panel`: `#e8ecf2`
     - `html:not(.dark) input:not([type="checkbox"]):not([type="radio"])`, `select`, `textarea`: `#ffffff`
     - `html:not(.dark) #tab-categories.bg-white`, `#tab-timeline.bg-white`: `#ffffff !important`
     - `html:not(.dark) .house-card`, `.category-folder-card`: `#fbfcfd` with subtle dual-layer shadow
2. **`dist/win-x64/wwwroot/css/styles.css`**:
   - Mirrored changes with 100% byte parity.
3. **`tests/web/components/light_mode_eye_comfort.test.js`**:
   - Created automated unit test suite covering `:root` tokens, `html:not(.dark)` surface rules, active tab contrast override, dark mode preservation, and stylesheet parity.

## 3. Verification Results
- **Web Vitest Suite**: 30 / 30 test files passed (330 / 330 tests passed), including all 10 tests in `light_mode_eye_comfort.test.js` and all 27 tests in `dark_mode_and_tablet.test.js`.
- **.NET xUnit Suite**: 161 / 161 tests passed in `HousingApplication.Tests.csproj`.
- **Stylesheet Parity**: `diff -u` between `src/.../styles.css` and `dist/.../styles.css` returned 0 differences.
