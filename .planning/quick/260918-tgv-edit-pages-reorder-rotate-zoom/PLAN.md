# Quick Task 260918-tgv: Edit Pages Multi-Page Drag & Drop Reordering, Page Rotation, and Dynamic Canvas Zoom

**Status:** Executing
**Created:** 2026-09-18
**Mode:** Quick

## User Intent
1. **Multi-Page Drag & Drop & Arbitrary Movement**: Enable selecting multiple pages and dragging them together to any arbitrary position in the document (moving multiple steps at once, eliminating tedious single-step arrow button clicking).
2. **Page Rotation & Permanent Saving**: Allow rotating individual pages or multi-selected pages by 90° clockwise with visual preview and permanent backend PDF saving.
3. **Responsive Card Zooming**: Polish and fix the canvas zoom controls (+/-, reset 100%, Ctrl+, Ctrl+Scroll) in Edit Pages so cards dynamically scale from 70% to 210% without rigid Tailwind column clamping.

## Tasks

### Task 1: Backend Page Rotation Support
- Add `Rotations` property to `ReorderPagesRequestDto` and create `RotatePagesRequestDto` / `RotatePagesResponseDto` in `DTOs.cs`.
- Implement `RotatePagesAsync` in `IFileOrganizerRepository` and `FileOrganizerRepository.cs` using `PdfSharpCore` (`page.Rotate = (page.Rotate + angle) % 360`).
- Also update `ReorderPagesAsync` to apply optional rotations during reordering.
- Expose endpoints in `Program.cs`:
  - `POST /api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/rotate-pages`
  - `POST /api/documents/{vaultId}/rotate-pages`
- Add C# backend tests in `ApiEndpointTests.cs` and `RepositoryTests.cs`.

### Task 2: Frontend Drag & Drop Multi-Page Reordering, Page Rotation, and Dynamic Zoom
- In `index.html`:
  - Remove rigid `grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5` from `#page-editor-grid`, using `.editor-grid-dynamic`.
  - Add "Rotate Selected" button (`btn-editor-rotate-selected`) to bottom sticky toolbar in `#doc-page-editor-modal`.
- In `styles.css`:
  - Add styles for drag-and-drop placeholder, drop indicator line (`.page-drop-indicator-left`, `.page-drop-indicator-right`), dragging cards opacity, and rotation transitions.
- In `doc-page-editor.js`:
  - Implement HTML5 and touch drag & drop for page cards (`handlePageDragStart`, `handlePageDragOver`, `handlePageDrop`, `handlePageDragEnd`).
  - Support multi-page drag: if dragged card is part of multi-selection, drag and move all selected cards as a contiguous block to the target position.
  - Add Rotate button (`btn-card-rotate`) on each page card header.
  - Implement `rotatePage(pageNum, angleDelta)` and `rotateSelectedPages(angleDelta)`.
  - Provide instant visual rotation via CSS and call backend `rotate-pages` API to permanently save the rotation into the PDF file.
  - Reload PDF with cache-busting so thumbnails and viewer reflect the saved rotation.
  - Ensure zoom controls scale `#page-editor-grid` smoothly across all 7 levels (`70%` to `210%`).

### Task 3: Unit Tests, Verification & Sync
- Update `tests/web/components/doc_page_editor.test.js`:
  - Test multi-page drag and drop reordering.
  - Test single-page arbitrary drag and drop insertion.
  - Test page rotation (card rotate button and multi-page rotate button).
  - Test rotate-pages API calls.
  - Test canvas zoom controls and dynamic grid sizing.
- Run full Vitest suite (`npm test`) and C# backend tests (`dotnet test`).
- Sync assets to `dist/win-x64/wwwroot/`.
- Update docs and STATE.md.
