---
status: resolved
trigger: "by default the notes should be empty (right now there is a placeholder text that says separated from so and so..). I don't want that."
created: 2026-09-17
updated: 2026-09-17
---

## Symptoms
- Expected: In the Separate & Move Pages submodal, the Notes input field should be completely empty by default.
- Actual: The Notes input field was prefilled with `Separated from ${activeEditorDoc.brief_arabic_title || activeEditorDoc.filename || 'document'}`.

## Root Cause
In `doc-page-editor.js` (`openExtractSubmodal`), lines 784-786 explicitly set:
`extractNotesInput.value = \`Separated from \${activeEditorDoc.brief_arabic_title || activeEditorDoc.filename || 'document'}\`;`
This auto-populated the input field with hardcoded English text instead of leaving it empty for the user.

## Resolution
1. In `src/HousingApplication.Web/wwwroot/js/doc-page-editor.js` and `dist/win-x64/wwwroot/js/doc-page-editor.js`:
   - Changed `openExtractSubmodal()` to set `extractNotesInput.value = '';`.
2. In `src/HousingApplication.Web/wwwroot/index.html` and `dist/win-x64/wwwroot/index.html`:
   - Updated placeholder to clean optional label: `placeholder="ملاحظات (اختياري)..."`.
3. In `tests/web/components/doc_page_editor.test.js`:
   - Added unit test: `'leaves extract-target-notes completely empty by default when opening extract submodal'`.
4. Verified:
   - Vitest unit tests pass 100% across all 20 tests in `doc_page_editor.test.js`.
