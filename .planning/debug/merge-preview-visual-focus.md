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

## Resolution
1. In `src/HousingApplication.Web/wwwroot/index.html`:
   - Expanded merge modal dialog container to `max-w-2xl sm:max-w-3xl max-h-[92vh]` for a spacious, modern view.
   - Updated Step 1 header from "ترتيب تسلسل الصفحات • Page Sequence" to "ترتيب المستندات • Reorder Documents".
   - Converted `#merge-docs-list` container from a vertical row stack to a responsive visual card grid (`grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3`).
   - Updated Step 2 banner header from "معاينة المستندات المدمجة • Merged Document Sequence" to "معاينة المستندات • Document Preview".
2. In `src/HousingApplication.Web/wwwroot/js/doc-manager.js`:
   - Step 1 (`renderMergeDocsList`): Replaced the text list with visual document cards styled exactly like `createPageCard` in `doc-page-editor.js`. Each card has a clean top bar (`#idx`, `◄` / `►` reorder buttons, `✕` remove button), a large thumbnail body (`min-h-[160px] sm:min-h-[190px]`, rendered with `width = 180`), and a quiet 1-line footer (`text-[11px] font-medium truncate`).
   - Step 2 (`updateMergeOrderSummary`): Redesigned preview cards to `w-52 sm:w-60` with large thumbnail containers (`min-h-[210px] sm:min-h-[250px]`), rendering high-DPI PDF thumbnails (`width = 220, height = 280`), and moving the document title to a subtle 1-line footer so the document image is the undeniable visual centerpiece.
   - Preserved all existing CSS class names (`.merge-preview-card`, `.merge-card-thumbnail`, `.merge-thumbnail-mini`, `.btn-merge-inline-swap`, `#merge-order-summary`) and DOM interactions to guarantee full backward and test compatibility.
3. Synchronized identical copies of modified assets to `dist/win-x64/wwwroot/`.
4. Verification:
   - 17/17 tests in `tests/web/components/merge_documents.test.js` passed.
   - Full Vitest suite across all 42 test files (601 tests) passed with 0 failures.
   - Web server verified running with `HTTP/1.1 200 OK` on `http://localhost:5000`.
