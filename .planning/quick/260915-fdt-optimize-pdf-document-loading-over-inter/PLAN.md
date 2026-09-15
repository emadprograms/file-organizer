---
status: complete
quick_id: 260915-fdt
slug: optimize-pdf-document-loading-over-inter
date: 2026-09-15
description: Optimize PDF document loading performance over internet connections
---

# Plan: Optimize PDF Document Loading Performance Over Internet Connections

## User Intent
When viewing documents over the internet (specifically in Tab / tablet mode), documents took 5-10+ seconds to load even though PDFs are only 600KB - 2MB.
Root causes identified:
1. `Program.cs` served all static assets with `Cache-Control: no-cache, no-store, must-revalidate`, forcing the browser to re-download 4.5MB of PDF.js scripts (`pdf.worker.js` ~2MB, `pdf.js` ~570KB, `viewer.js` ~440KB, fonts) on every single document click.
2. `doc-viewer.js` re-navigated `pdfFrame.src = viewer.html?file=...` on every document click instead of reusing the active PDF.js viewer instance via `PDFViewerApplication.open({ url: pdfUrl })`, causing worker destruction and full JavaScript re-compilation.
3. `/api/pdf/...` endpoints lacked HTTP caching headers (`Cache-Control`, `ETag`, `Last-Modified`), forcing full re-downloads even for previously opened immutable vault documents.
4. Response compression was not enabled in ASP.NET Core for static vendor libraries.

## Key Changes
1. `Program.cs`:
   - Add `builder.Services.AddResponseCompression()` and `app.UseResponseCompression()`.
   - Differentiate static file caching in `app.UseStaticFiles()`: provide long-term immutable caching (`public, max-age=31536000, immutable`) for `/lib/` (specifically PDF.js vendor assets and fonts), while retaining no-cache/revalidation for application scripts.
   - Add HTTP caching headers (`Cache-Control: private, max-age=604800, stale-while-revalidate=86400`, `Last-Modified`, and `ETag`) to `/api/pdf/{vaultId}` and `/api/areas/{areaId}/houses/{houseId}/pdf/{vaultId}`.
2. `doc-viewer.js`:
   - In `openDocument` / `peekDocument`, check if `pdfFrame.contentWindow.PDFViewerApplication` is already available and initialized in Tab mode.
   - If available, call `pdfFrame.contentWindow.PDFViewerApplication.open({ url: pdfUrl })` directly instead of re-navigating `pdfFrame.src`.
   - Fall back to standard src assignment when initializing the viewer for the first time or if PDF.js is not yet active.
3. Asset Synchronization & Testing:
   - Synchronize modified web assets to `dist/win-x64/wwwroot/`.
   - Add unit tests verifying the caching headers, compression, and viewer instance reuse.
   - Verify all existing .NET and Vitest test suites pass with 100% success.
   - Update documentation (`STATE.md`, `SUMMARY.md`), commit and push.
