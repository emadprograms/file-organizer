# Quick Task: 260915-fdt Optimize PDF Document Loading Performance Over Internet Connections

## Overview
Resolved major document viewing performance bottlenecks when accessing the application over the internet (specifically on tablets/iPad/Android using Tab mode and remote desktop browsers). Replaced heavy repetitive script transfers and iframe teardowns with aggressive vendor library caching, persistent PDFViewerApplication instance reuse, response compression, and immutable document caching headers.

## Root Causes Addressed
1. **Uncached Vendor Libraries**: `Program.cs` previously served all static files with `Cache-Control: no-cache, no-store, must-revalidate`. On tablets requiring Mozilla's PDF.js Tab mode (`viewer.html`), the browser had to re-download ~4.5 MB of uncompressed JavaScript and fonts (`pdf.worker.js` ~2 MB, `pdf.js` ~570 KB, `viewer.js` ~440 KB, fonts ~600 KB) on every single document click.
2. **Iframe Destruction & Web Worker Teardown**: `doc-viewer.js` previously set `pdfFrame.src = viewer.html?file=...` on every document click, destroying the active iframe and forcing the tablet to re-parse 4.5 MB of JavaScript and spawn a new Web Worker thread on every document click.
3. **Missing PDF Caching Headers**: `/api/pdf/{vaultId}` and `/api/areas/{areaId}/houses/{houseId}/pdf/{vaultId}` returned raw files without `Cache-Control`, `ETag`, or `Last-Modified`, preventing browsers from caching immutable vault documents locally or validating with conditional GET (304 Not Modified).
4. **Uncompressed Static Delivery**: Response compression was not registered in ASP.NET Core for static vendor dependencies.

## Key Changes
1. **Vendor Library Caching & Response Compression (`src/HousingApplication.Web/Program.cs`)**:
   - Registered `builder.Services.AddResponseCompression(options => { options.EnableForHttps = true; })` and `app.UseResponseCompression()`.
   - Updated `app.UseStaticFiles()` to apply long-term immutable caching (`Cache-Control: public, max-age=31536000, immutable`) for all vendor assets under `/lib/` (specifically `pdfjs`), while maintaining strict revalidation headers for application code (`/js/`, `/css/`).
2. **Document Streaming Caching & Conditional GET (`src/HousingApplication.Web/Program.cs`)**:
   - Added `Cache-Control: private, max-age=604800, stale-while-revalidate=86400` to both `/api/pdf/{vaultId}` and `/api/areas/{areaId}/houses/{houseId}/pdf/{vaultId}`.
   - Supplied `lastModified` (`fileInfo.LastWriteTimeUtc`) and `entityTag` (`new EntityTagHeaderValue($"\"{fileInfo.Length}_{lastModified.Ticks}\"")`) to `Results.File`.
   - Enabled native HTTP 304 Not Modified conditional requests for returning visitors.
3. **Tab Mode PDFViewerApplication Instance Reuse (`src/HousingApplication.Web/wwwroot/js/doc-viewer.js` & `dist/win-x64/wwwroot/js/doc-viewer.js`)**:
   - Added `loadPdfIntoFrame(pdfFrame, pdfUrl)` helper:
     - Detects if `pdfFrame.contentWindow.PDFViewerApplication` is already loaded and initialized.
     - Calls `PDFViewerApplication.open({ url: pdfUrl })` directly without re-navigating or reloading the iframe.
     - Falls back to `pdfFrame.src = targetSrc` only on initial viewer creation or mode switch.
4. **Automated Verification**:
   - Added unit test in `tests/web/components/doc_viewer.test.js` verifying that `openDocument` in Tab mode reuses the initialized `PDFViewerApplication` instance and preserves `pdfFrame.src`.
   - Added assertions in `tests/HousingApplication.Tests/ApiEndpointTests.cs` verifying `Cache-Control`, `ETag`, and conditional GET returning HTTP 304 Not Modified on `/api/pdf/{vaultId}`.

## Test Results
- **Vitest Frontend Tests**: 436 tests passing across 36 test files (100%).
- **.NET Unit & Integration Tests**: 926 tests passing in `HousingApplication.Tests` (100%).
