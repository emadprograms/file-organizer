---
status: complete
task_id: 260914-aq4
slug: when-you-enter-any-house-the-right-side-
date: 2026-09-14
---

# Quick Task Summary: Right-Side Document Preview Empty State & Guidance

**Task ID**: `260914-aq4`  
**Status**: Complete  
**Date**: 2026-09-14  

---

## 1. Overview
Addressed user feedback where entering any house (`#/house/...`) left the right two-thirds of the screen completely empty and plain white without explanation:
- Added `#document-empty-state` placeholder container in `index.html` (both `src` and `dist`) that renders whenever a house is selected before a document is opened.
- Styled `#document-empty-state` with eye-comfort light grey canvas (`#edf0f4` in light mode) and deep dark canvas (`#080c14` in dark mode) to eliminate blinding white space.
- Formatted clean, non-wordy minimalist bilingual guidance under an understated muted icon:
  - English: "Select a document to preview"
  - Arabic: "اختر مستنداً للمعاينة"
  - Avoided wordy paragraphs, heavy dashed boxes, and redundant explanatory sentences in line with the application's clean design principles.
- Integrated reactive view management across `router.js`, `doc-viewer.js`, `area-grid.js`, and `tenant-manager.js`:
  - `selectHouse`: hides welcome panel, shows document empty state.
  - `openDocument` & `peekDocument`: hides empty state, displays document viewer.
  - `closeDocument`: if viewing an active house, restores empty state; if not in a house, restores welcome panel.
  - `renderAreaGrid` & `switchToViewMode`: hides empty state when viewing area overview or database inspector.
- Preserved 100% byte-for-byte asset parity between `src/HousingApplication.Web/wwwroot/` and `dist/win-x64/wwwroot/`.
- Created automated test suite `tests/web/components/document_empty_state.test.js` validating markup, styles, and lifecycle transitions.

## 2. Changes Made
1. **`src/HousingApplication.Web/wwwroot/index.html` & `dist/win-x64/wwwroot/index.html`**:
   - Added `#document-empty-state` placeholder card with icon and bilingual text prompts.
2. **`src/HousingApplication.Web/wwwroot/css/styles.css` & `dist/win-x64/wwwroot/css/styles.css`**:
   - Added `html:not(.dark) #document-empty-state { background-color: #edf0f4; }`
   - Added `html.dark #document-empty-state { background-color: #080c14; }`
3. **`src/HousingApplication.Web/wwwroot/js/router.js` & `dist/win-x64/wwwroot/js/router.js`**:
   - Shows `#document-empty-state` when selecting a house; hides it when switching to DB inspector or overview.
4. **`src/HousingApplication.Web/wwwroot/js/doc-viewer.js` & `dist/win-x64/wwwroot/js/doc-viewer.js`**:
   - Hides `#document-empty-state` when opening or peeking a document.
   - Restores `#document-empty-state` on `closeDocument()` if a house is active.
5. **`src/HousingApplication.Web/wwwroot/js/area-grid.js` & `tenant-manager.js` (and dist)**:
   - Ensures `#document-empty-state` is hidden when switching views back to Area Grid overview.
6. **`tests/web/components/document_empty_state.test.js`**:
   - Automated unit test suite with 9 tests verifying HTML, CSS, and transition states.

## 3. Verification Results
- **Vitest Suite**: 31 / 31 test files passed (348 / 348 tests passed).
- **Parity Verification**: Exact 1:1 match verified across all modified files between `src/HousingApplication.Web/wwwroot` and `dist/win-x64/wwwroot`.
