---
status: resolved
trigger: "is it not possible to get an intuitive style merging instead of this weird text written jargon. like.. I select two documents (with the check button) and click on merge. and it asks me where do I want to save and the name (it take the name of first selected document by default), and takes the date and other properties of the first selected document. isn't that much simpler. If the user selects more than two, then it just opens the rearrangement box (just like the one for edit pages) and allows you to re-arrange first."
created: 2026-09-17
updated: 2026-09-17
slug: intuitive-merge-modal-ux
---

# Debug & UX Overhaul: Streamline Document Merge Flow & Intuitive Multi-Doc Rearrangement

## Symptoms
- **Expected Behavior**: Merging 2 documents should be effortless, matching the compact and intuitive style of Batch Move and Batch Copy modals (`max-w-md`):
  - Select 2 documents and click merge -> asks only where to save (target category and tenant) and the name (defaulting to the first selected document's name).
  - Date and other properties are automatically inherited from the first selected document.
  - If more than two documents are selected (> 2), opens a clean rearrangement box first (just like edit pages) allowing the user to re-arrange before proceeding to save.
- **Actual Behavior**: The merge modal was oversized (`max-w-xl`), contained dense explanatory text jargon ("تسلسل المستندات المدمجة", "استخدم أزرار الأسهم...", long note disclaimers), showed unnecessary manual date and notes input fields, combined multi-doc adding and reordering into one cluttered screen, and defaulted to an awkward concatenated title instead of adopting the first document's name.

## Root Cause
- `src/HousingApplication.Web/wwwroot/index.html` and `src/HousingApplication.Web/wwwroot/js/doc-manager.js` implemented a monolithic all-in-one merge dialog with excessive explanatory paragraphs and manual form fields, instead of an adaptive 2-step / direct-save workflow.

## Resolution
1. **Redesigned `#merge-docs-modal` in `index.html`**:
   - Size: `max-w-md` (compact and sleek, identical to `batch-move-modal` and `batch-copy-modal`).
   - Removed all weird text written jargon, redundant date/notes fields, and verbose explanations.
   - 2 clean contextual steps (Multi-Select Only):
     - `#merge-step-save`: Direct Save & Name screen (Document Name prefilled from doc 1, Target Category prefilled from doc 1, Target Tenant prefilled from doc 1, date/properties automatically inherited, clean order pill with `⇄ Swap` button, single-line delete sources checkbox).
     - `#merge-step-reorder`: Clean visual rearrangement box for > 2 documents (with number badges, titles, page counts, `▲`/`▼` controls), and `Continue →` button.
   - Removed `#merge-step-pick`, `#merge-add-doc-container`, and `#merge-save-add-doc-container`.
2. **Removed Single-Document Merge Triggers**:
   - Removed `#viewer-merge-btn` from Document Viewer toolbar (`index.html` and `doc-viewer.js`).
   - Removed `.doc-menu-item-merge` from 3-dots dropdown context menu (`doc-manager.js`).
   - Removed `#btn-doc-merge` from Document Action modal (`index.html` and `doc-manager.js`).
   - Merging is now triggered exclusively via multi-selection checkboxes in the category/document lists when $\ge 2$ documents are selected.
3. **Fixed "Delete Selected" Disappearance Regression**:
   - In `categories-view.js` and `doc-manager.js`, `isRestricted` evaluated to `undefined` or `null` when `window.authManager` was uninitialized, which caused DOM `classList.toggle('hidden', undefined)` to treat the call as having no force argument and toggle visibility on every click.
   - Wrapped `isRestricted` in `Boolean(...)` to ensure strict boolean values.
4. **Verification**:
   - 15/15 Vitest tests in `tests/web/components/merge_documents.test.js` passed.
   - 26/26 Vitest tests in `tests/web/components/batch_operations.test.js` passed.
   - 571/571 Vitest tests across all 42 suites passed.
   - 970/970 .NET backend tests passed.
   - 100% byte parity synchronized to `dist/win-x64/wwwroot/`.
