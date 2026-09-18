---
status: in_progress
trigger: "sometimes when I'm on tab scrolling the document. it resets the view. take a look at this."
created: 2026-09-18
updated: 2026-09-18
---

## Current Focus
- hypothesis: "When scrolling a document on tablet mode, dynamic browser toolbar collapse/expand (or orientation changes) fires window resize events in the PDF.js iframe. In viewer.js, webViewerResize() invokes pdfViewer.currentScaleValue = currentScaleValue with noScroll: false. This triggers scrollPageIntoView which, when scale is 'page-fit' (the default tablet zoom mode) or when location is stale/null during continuous touch scrolling, resets the container scrollTop back to the top of page 1. Additionally, loadPdfIntoFrame in doc-viewer.js attaches duplicated pagesloaded and documentinit event listeners and fires delayed timeouts (50ms, 200ms) that re-apply currentScaleValue while touch scrolling is underway."
- test: "Verify webViewerResize preserves container.scrollTop using setScale({ noScroll: true }) and proportional scroll offset adjustment. Verify doc-viewer.js deduplicates listeners and prevents re-applying zoom if already matching or if container has scrolled."
- next_action: "Apply fix to viewer.js and doc-viewer.js in both src and dist, add regression tests, and run Vitest."
