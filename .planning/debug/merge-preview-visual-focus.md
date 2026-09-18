---
status: resolved
trigger: "I'm still seeing that page sequence thing. the images are literally barely visible. the main focus should be on the images not the title, like how it is in edit & split pages."
created: 2026-09-18
updated: 2026-09-18
slug: merge-preview-visual-focus
---

# Debug & UI Enhancement: Merge Modal Visual Focus on Document Previews

## Symptoms
- User reports seeing "that page sequence thing" in the merge modal.
- The thumbnail images were tiny and "barely visible" (120px in save step, 40px in reorder list).
- Text and titles dominated the cards and modal rather than the preview images.
- Expected behavior: Match the visual style of "Edit & Split pages" (`doc-page-editor.js`), where large, high-resolution document page images are the primary focus of the card, headers avoid "Page Sequence" jargon, and titles/details are presented as subtle footers.

## Root Cause
1. Modal width was constrained to `max-w-lg` (512px), forcing preview cards to be narrow (`w-36`, 144px).
2. Thumbnail container was sized to `w-30 h-38` (120px x 152px), and rendered with small target width (120px), leaving images tiny on high-DPI screens and tablets.
3. Card layout placed large, bold titles and categories prominently, visually overpowering the preview thumbnail.
4. Step 1 (reorder step for >2 docs) was titled "ترتيب تسلسل الصفحات • Page Sequence" and rendered as a dense vertical text list with tiny 40px thumbnails instead of an image-focused visual card grid like `doc-page-editor`.
5. Step 2 banner was titled "معاينة المستندات المدمجة • Merged Document Sequence".

## Resolution (Option A - Matching Edit Pages Layout)
1. In `src/HousingApplication.Web/wwwroot/index.html`:
   - Expanded `#merge-docs-modal` container to `w-full max-w-5xl h-[92vh] max-h-[900px] flex flex-col overflow-hidden` matching `doc-page-editor-modal`.
   - Updated modal header with document counter badge, dark styling, and close button.
   - Styled Step 1 (`#merge-step-reorder`) and Step 2 (`#merge-step-save`) with a full-height scrollable preview viewport (`flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-100 dark:bg-slate-950`) and responsive grid layout.
   - Positioned target save settings (Document Name, Category Folder, Tenant, Delete sources checkbox) and action buttons in a sticky bottom action bar (`bg-white dark:bg-slate-900 border-t shadow-lg`).
2. In `src/HousingApplication.Web/wwwroot/js/doc-manager.js`:
   - Updated `updateMergeOrderSummary()` to render document cards with on-card reorder controls (`◄` / `►`) directly in each card's header bar, matching `createPageCard` from `doc-page-editor.js`.
   - Cards display large, high-resolution preview thumbnails (`min-h-[200px] sm:min-h-[260px]`, rendering at 240x300) with a subtle 1-line title and page count footer.
   - Added interactive reorder handlers (`btn-card-move-left` and `btn-card-move-right`) dynamically invoking document shift operations and updating live state.
   - Updated `renderMergeDocsList()` to provide the same card-based visual design with on-card remove and reorder controls.
   - Preserved all selector classes (`.merge-preview-card`, `.merge-card-thumbnail`, `.merge-thumbnail-mini`, `.btn-merge-inline-swap`, `#merge-order-summary`) ensuring 100% backward and test compatibility.
3. Synchronized identical copies of modified assets to `dist/win-x64/wwwroot/`.
4. Verification:
   - 17/17 tests in `tests/web/components/merge_documents.test.js` passed.
   - Full Vitest suite across all 42 test files (601 tests) passed with 0 failures.
   - Web server verified running with `HTTP/1.1 200 OK` on `http://localhost:5000`.
