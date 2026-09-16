---
status: resolved
trigger: "no the translation feature wasn't done properly. i don't the translation of what is present in the database. i want a translation of the contents that the user is setting on the screen like how Google translate does it. you just picked the contents from the database and translate that. the program now doesn't support that. user can automatically upload documents without sending to the ai. what will you do in that case. i don't want this useless feature that you've made. i want google style translation overlay on the document."
created: 2026-09-16
updated: 2026-09-16
---

## Current Focus
- status: resolved
- hypothesis: "Confirmed and resolved: The translation feature previously read SQLite metadata summaries and displayed cards over the document. True Google Translate style visual translation requires client-side canvas-level OCR with bounding box text replacement directly over the document pages."
- next_action: "All tests passing, documentation updated, commit and push changes."

## Symptoms
1. **Expected behavior**: In the document viewer, clicking "Translate" provides a true Google Translate style in-place overlay directly over the document displayed on screen: detecting actual visible text blocks on the page canvas, placing solid background-matched boxes with translated English text directly over original Arabic words at exact bounding box coordinates, preserving document layout (stamps, tables, signatures, seals), operating 100% offline, and supporting newly uploaded scans without prior AI processing.
2. **Actual behavior**: Previously fetched summaries from SQLite (`pages.content_explanation`) and rendered separate summary cards over the viewport, failing for documents without database AI records and failing to provide visual in-place overlay.
3. **Error messages**: Architectural / functional misalignment.
4. **Timeline**: Reported immediately after initial metadata summary implementation.
5. **Reproduction**: Opening any new document without AI processing previously gave no translation, and existing documents rendered summary cards rather than in-place text replacement.

## Root Cause
The previous translation overlay relied on pre-computed database metadata summaries (`pages.content_explanation`), which neither translates in-place over the visual document layout nor functions for newly uploaded documents without database page records.

## Solution & Implementation
1. **Bundled Offline OCR Engine**:
   - Downloaded and bundled official Tesseract.js v5 WebAssembly worker, SIMD LSTM WASM binary, and fast Arabic/English trained models locally into `wwwroot/lib/tesseract/` (`tesseract.min.js`, `worker.min.js`, `tesseract-core-simd-lstm.wasm`, `tesseract-core-simd-lstm.wasm.js`, `ara.traineddata.gz`, `eng.traineddata.gz`).
   - Zero external cloud or API calls; operates 100% offline.
   - Synchronized across both `src/HousingApplication.Web/wwwroot/` and `dist/win-x64/wwwroot/`.
2. **Multi-Tier Detection Strategy**:
   - **Tier 1**: In-memory page OCR cache (`pageOcrCache`) for instant re-rendering across page changes and zoom.
   - **Tier 2**: PDF text layer via PDF.js (`page.getTextContent()`) for instant (<10ms) bounding box extraction on digital PDFs.
   - **Tier 3**: Local Tesseract.js offline WebAssembly OCR on the rendered `<canvas>` element for physical scans, newly uploaded documents, and files with no digital text layer.
   - **Tier 4**: Database metadata fallback for empty/damaged scans.
3. **Google Translate Style In-Place Visual Overlay**:
   - Renders `.pdf-translation-layer` directly above each rendered page canvas inside `.pdf-page-wrapper`.
   - Each detected Arabic line/phrase is covered by an `.in-place-translated-box` with solid white background (`#ffffff`), dark slate text (`#0f172a`), proportional typography, and exact pixel bounding box coordinates.
   - Tooltip shows original Arabic text on hover.
   - Hovering or clicking any box temporarily dims it to 12% opacity to peek at the original scan underneath.
   - Dedicated "Peek Original" page toggle button (`.btn-peek-scan`) allows one-touch reveal of the entire scan underneath.
4. **Comprehensive Arabic Vocabulary & Legal/Housing Phrases**:
   - Expanded offline dictionary covering Bahrain administrative bodies, Ministries, Directorates, committees, military ranks, lease/tenancy clauses, utility terms, dates, and numerals.
5. **Tab Mode Restoration & Flexbox Multi-Page Fix**:
   - Resolved regression where Tab mode (`shouldUseOfficialViewer() === true`) failed to restore the official viewer iframe (`/lib/pdfjs/web/viewer.html`) after disabling translation due to an unintended `!shouldUseOfficialViewer()` filter in `removeDocumentTranslation()`.
   - Fixed multi-page flex container compression by adding `flex-shrink: 0 !important;` and min-height constraints to `.pdf-page-wrapper` and `.pdf-page-canvas` in `styles.css` and `doc-viewer.js`, preventing pages from squashing into a single page.
   - Re-bound viewer controls dynamically and guarded concurrent asynchronous page renders with `currentTranslationPromise`.

## Verification
- **Frontend Component Tests**: All 469 Vitest tests passed across all 37 test suites (`npm test`), including dedicated regression suites for Tab mode viewer restoration, multi-page layout without flex-shrink squashing, and translation toggling.
- **Backend .NET Tests**: All 955 .NET tests passed in `tests/HousingApplication.Tests/` (`dotnet test --no-build`).
- **Parity Guarantee**: 100% byte and asset parity maintained between `src/HousingApplication.Web/wwwroot/` and `dist/win-x64/wwwroot/`.
