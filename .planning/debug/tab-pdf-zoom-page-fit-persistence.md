---
status: resolved
trigger: "When I'm on my tab and I only want to view the documents in AP fit format and not automatic zoom there is no way to tell the program to remember it for example if I make the change on one document and I move to the next document it automatically reverts to automatic zoom I do not want that if I have set the settings to Page Fit it should remain page fit"
created: 2026-09-17
updated: 2026-09-17
resolved: 2026-09-17
---

## Current Focus
- hypothesis: "In the tab presenter (PDF.js viewer.js / viewer.html), scale changes are dispatched to webViewerScaleChanged but never persisted to localStorage or AppOptions defaultZoomValue. Furthermore, when switching documents via PDFViewerApplication.open(), toolbar.reset() unconditionally resets the dropdown to DEFAULT_SCALE_VALUE ('auto'), and setInitialView resets currentScaleValue to 'auto'. In the parent window (doc-viewer.js), resolveViewerSrc does not pass the user's preferred zoom in the hash or enforce it upon opening new documents."
- next_action: "Examine PDF.js scale change and reset paths, implement zoom preference persistence in localStorage and AppOptions across both viewer.js and doc-viewer.js, support both Page Fit ('page-fit') and native Computer mode ('#view=Fit'), synchronize dist assets, and verify with unit tests."

## Symptoms
- **Expected behavior**: When the user selects "Page Fit" (or any zoom mode) on a tablet or desktop, the viewer should remember this choice. Navigating to the next document should open it in "Page Fit" format, preserving the user's zoom preference.
- **Actual behavior**: When moving to the next document, the viewer automatically reverts to "Automatic Zoom", forcing the user to re-select "Page Fit" on every document.
- **Environment**: Tablet presenter (PDF.js official viewer in iframe) and Computer mode (native iframe viewer).

## Root Cause Analysis
1. `src/HousingApplication.Web/wwwroot/lib/pdfjs/web/viewer.js`:
   - In `webViewerScaleChanged(evt)` (line 1883), `PDFViewerApplication.pdfViewer.currentScaleValue = evt.value;` is set in memory only. No persistence is saved to `localStorage` or `AppOptions.set("defaultZoomValue", evt.value)`.
   - In `PDFViewerApplication.toolbar.reset()` (line 12291), `this.pageScaleValue = _ui_utils.DEFAULT_SCALE_VALUE;` (`"auto"`) is unconditionally applied when a document closes.
   - In `PDFViewerApplication.setInitialView()` (line 1304), if no hash zoom is provided, `this.pdfViewer.currentScaleValue = _ui_utils.DEFAULT_SCALE_VALUE` (`"auto"`).
   - In `PDFLinkService.setHash()` (line 3607), `"page-fit"` is not recognized in `!zoomArg.includes("Fit")` logic as a valid destination, so passing `#zoom=page-fit` would trigger an invalid zoom error unless mapped to `"Fit"`.
2. `src/HousingApplication.Web/wwwroot/js/doc-viewer.js`:
   - `resolveViewerSrc(pdfUrl)` generates `/lib/pdfjs/web/viewer.html?file=...` without specifying `#zoom=page-fit` or reading user preferences.
   - `loadPdfIntoFrame` reuses the iframe viewer via `PDFViewerApplication.open({ url: pdfUrl })` without maintaining or restoring the user's scale preference.
   - In Computer mode, `resolveViewerSrc` hardcodes `#view=FitH` (Fit Width / horizontal) instead of respecting Page Fit (`#view=Fit`).
