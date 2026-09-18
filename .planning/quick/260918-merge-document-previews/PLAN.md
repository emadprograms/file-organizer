---
status: completed
quick_id: 260918-merge-document-previews
slug: merge-document-previews
date: 2026-09-18
description: Display visual document page previews instead of plain text names and arrows in the merge modal
---

# Plan: Visual Document Previews for Document Merge

## User Intent
When merging documents, replace the text-heavy name and arrow display (`Doc 1 → Doc 2`) with real visual document page previews/thumbnails so the user can visually identify and verify the documents being merged at a glance without reading through lengthy text titles.

## Architecture & Implementation Plan

1. **Modal Layout & Preview Cards in `index.html`**:
   - Update `#merge-docs-modal` (expand slightly from `max-w-md` to `max-w-lg` for comfortable preview display, while maintaining compact mobile responsiveness).
   - In `#merge-step-save`:
     - Replace `#merge-order-banner` with a dedicated `#merge-preview-container`:
       - For 2 documents: A side-by-side visual preview comparison with:
         - **Card 1**: Position badge (`1` / `أولاً`), A4-proportioned thumbnail container (`.merge-preview-thumbnail`), document title, and page count badge.
         - **Center Swap Action**: Modern circular/pill swap button (`#btn-merge-swap-order`) with `⇄` icon.
         - **Card 2**: Position badge (`2` / `ثانياً`), A4-proportioned thumbnail container, document title, and page count badge.
       - For > 2 documents: A sleek horizontal scrollable sequence of preview cards showing the exact merged order.
   - In `#merge-step-reorder`:
     - Enhance `#merge-docs-list` items to include a rendered document thumbnail alongside the sequence number, title, and `▲`/`▼` controls.

2. **Asynchronous PDF Thumbnail Rendering in `doc-manager.js`**:
   - Implement `renderDocThumbnail(containerEl, vaultId, pageNum = 1)`:
     - Resolves the PDF stream URL using `resolvePdfUrl(vaultId)`.
     - Utilizes `pdfjsLib.getDocument({ url: pdfUrl })` to fetch and render page 1 onto an HTML `<canvas>`.
     - Caches thumbnail canvases or promises in memory so reordering / swapping is instantaneous and zero-flicker.
     - Gracefully falls back to a clean document icon placeholder when in test environments (jsdom) or if the PDF stream fails.
   - Update `renderMergeDocsList()` to instantiate thumbnail containers and call `renderDocThumbnail`.
   - Update `updateMergeOrderSummary()` / `renderMergePreviewBanner()`:
     - Render the visual preview cards in `#merge-preview-container`.
     - When `handleSwapMergeDocs()` is invoked, update the preview cards and re-render thumbnails smoothly.

3. **Styling & Dark Mode in `styles.css` / Tailwind**:
   - Ensure thumbnail containers have realistic sheet-of-paper styling (subtle shadow, rounded corners, dark mode surface backgrounds).
   - Touch and tablet friendly tap targets for swap and reorder.

4. **Testing & Verification**:
   - Update `tests/web/components/merge_documents.test.js` to assert the presence and behavior of `#merge-preview-container`, preview cards, thumbnail elements, and swap interactions.
   - Run all Vitest suites and backend tests to guarantee 100% pass rate.
   - Synchronize assets to `dist/win-x64/wwwroot/`.
