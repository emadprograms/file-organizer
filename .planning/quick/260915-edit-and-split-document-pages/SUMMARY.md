# Quick Task Summary: Interactive Document Page Editor, Page Separation, Reordering & Deletion (QCK-51)

**Quick Task ID:** `260915-edit-and-split-document-pages`  
**Date:** 2026-09-15  
**Author:** Antigravity  

---

## 1. Executive Summary

Implemented an interactive, touch-friendly **Document Page Editor** (`doc-page-editor.js`) allowing users on both **Computer (desktop)** and **Tab (tablet / touchscreen)** to visually view, reorder, delete, and separate/extract pages from multi-page documents.

### Key Problem Solved
Previously, multi-page PDF documents containing bundled distinct forms (e.g. a 4-page PDF containing a Maintenance letter, a Key Handover form, and a Rent Deduction letter) were locked together as a single immutable document. There was no way to:
- Separate a specific page (e.g. the Key Handover protocol) and move it into its rightful category (e.g. `04 - محضر تسليم مفتاح`) or assign it to a specific tenant.
- Delete unwanted or blank pages directly on tablet or desktop with 1 tap.
- Reorder pages within a document.

### Solution Overview
1. **Interactive Page Editor Modal (`#doc-page-editor-modal`)**:
   - Renders high-fidelity thumbnails of each page via PDF.js (with canvas fallback).
   - Each page card features 1-tap delete `🗑️` (with confirmation prompt), left/right reorder buttons `◀ ▶`, and tap-to-select checkbox pill.
   - Sticky bottom action bar with `Select All`, `Deselect`, `Delete Selected (N)`, and `Separate & Move (N)...`.
   - Touchscreen-first ergonomics: minimum touch targets $\ge 44\text{px}$, responsive grid (2 columns on mobile/mini-tablets, up to 5 on desktop), and clear touch affordances.

2. **"Separate & Move" Sub-Modal (`#extract-pages-submodal`)**:
   - Extracts selected pages from the source document into a brand new document.
   - Allows choosing target category (standard 01-13 categories or custom folder), assigning to any tenant in the house, specifying a custom Arabic document title, document date, and notes.
   - Atomically creates `vault/doc_{newVaultId}.pdf` containing the extracted pages, updates source PDF to retain remaining pages (or deletes source doc if all pages extracted), reassigns records in the database, and automatically loads the new document in the viewer.

3. **Multi-Point Discoverability**:
   - **Document Viewer Toolbar**: Prominent amber `✂️ Edit Pages` button in `#document-viewer-panel` header.
   - **Document 3-Dots Dropdown**: `✂️ Edit & Split Pages` action in context menus across Categories and Timeline views.
   - **Document Inspector / Spacebar Quick Look**: `✂️ Edit Pages` button in modal header.
   - **Document Action Modal**: Dedicated `✂️ Edit Pages` button in footer.

4. **100% Database Integrity & Lineage Preservation**:
   - Strict transactional integrity across `documents`, `pages`, and `batches` tables.
   - Decrements `documents.page_count` and `batches.page_count` on page deletion to prevent database/physical scan disparity.
   - When pages are extracted into a new document, the new document inherits `batch_id` from the source document, preserving provenance.
   - In SQLite, the `pages` table enforces `UNIQUE(batch_id, page_number)`. Reordering uses temporary negative sequencing to avoid unique constraint collisions, and extraction retains original physical `page_number` while updating `vault_id`, `category`, and `tenant_id`.

---

## 2. Changes Made

### A. Backend DTOs & Repository (`HousingApplication.Web`)
- `src/HousingApplication.Web/Models/DTOs.cs`:
  - `ExtractPagesRequestDto`, `ExtractPagesResponseDto`
  - `DeletePagesRequestDto`, `DeletePagesResponseDto`
  - `ReorderPagesRequestDto`, `ReorderPagesResponseDto`
- `src/HousingApplication.Web/Data/IFileOrganizerRepository.cs`:
  - `ExtractPagesAsync`, `DeletePagesAsync`, `ReorderPagesAsync`
- `src/HousingApplication.Web/Data/FileOrganizerRepository.cs`:
  - Implemented `ExtractPagesAsync`: uses `PdfSharpCore` to slice out requested pages into `vault/doc_{newVaultId}.pdf`, updates source PDF, updates `documents`, reassigns `pages.vault_id`, preserves batch lineage, and deletes source document if 0 pages remain.
  - Implemented `DeletePagesAsync`: trims physical PDF, deletes unlinked rows in `pages`, decrements `documents.page_count`, decrements `batches.page_count`, and deletes document if 0 pages remain.
  - Implemented `ReorderPagesAsync`: permutes physical PDF pages and updates `pages` table sequence with collision-free negative sequencing.
- `src/HousingApplication.Web/Program.cs`:
  - Added REST endpoints:
    - `POST /api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/extract-pages`
    - `POST /api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/delete-pages`
    - `POST /api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/reorder-pages`

### B. Frontend Components & User Interface
- `src/HousingApplication.Web/wwwroot/js/doc-page-editor.js`:
  - Component controller managing modal lifecycle, thumbnail rendering, selection state, 1-tap delete, reordering, and extraction sub-modal.
- `src/HousingApplication.Web/wwwroot/index.html`:
  - Added `#viewer-edit-pages-btn` into `#document-viewer-panel` header.
  - Added `#quick-look-edit-pages` into `#quick-look-modal` header.
  - Added `#btn-doc-edit-pages` into `#doc-action-modal` footer.
  - Added `#doc-page-editor-modal` container with Tailwind CSS styling and dark mode support.
  - Added `#extract-pages-submodal` container for target category/tenant/title configuration.
  - Registered `<script src="js/doc-page-editor.js?v=260915-01"></script>`.
- `src/HousingApplication.Web/wwwroot/js/doc-viewer.js`:
  - Bound `#viewer-edit-pages-btn` to `window.openPageEditor(currentPinnedDoc)`.
- `src/HousingApplication.Web/wwwroot/js/doc-manager.js`:
  - Added `✂️ Edit & Split Pages` (`.doc-menu-item-edit-pages`) to `openDocDropdownMenu`.
  - Bound `#btn-doc-edit-pages` in `initDocManager`.
- `src/HousingApplication.Web/wwwroot/js/pdf-preview.js`:
  - Bound `#quick-look-edit-pages` to `window.openPageEditor(...)`.
- `dist/win-x64/wwwroot/`:
  - Mirrored all updated assets to ensure 100% parity for native builds.

---

## 3. Verification & Testing

1. **Backend Unit & Integration Tests (`dotnet test`)**:
   - `RepositoryTests.cs`:
     - `ExtractPagesAsync_ExtractsPages_CreatesNewDocAndKeepsRemainingInSource`: verified physical file creation, `page_count` updates, batch lineage inheritance, and page re-indexing.
     - `ExtractPagesAsync_AllPagesExtracted_DeletesSourceDocument`: verified clean deletion of source doc when 100% of pages are extracted.
     - `DeletePagesAsync_RemovesPagesFromPdfAndDatabase_UpdatesPageCount`: verified physical PDF trimming, decrementing `documents.page_count` and `batches.page_count`.
     - `ReorderPagesAsync_ReordersPagesPhysicallyAndInDatabase`: verified page permutation and database sequence update.
   - `ApiEndpointTests.cs`:
     - `ExtractPages_ApiEndpoint_ReturnsSuccess`: verified HTTP 200 and response payload.
     - `DeletePages_ApiEndpoint_ReturnsSuccess`: verified HTTP 200 and remaining pages count.
     - `ReorderPages_ApiEndpoint_ReturnsSuccess`: verified HTTP 200.
   - **Result:** **933/933 .NET tests passed** (0 failed, 0 skipped).

2. **Frontend Vitest Component Tests (`npm test`)**:
   - `tests/web/components/doc_page_editor.test.js`:
     - Verified `index.html` contains all modal containers and trigger buttons.
     - Verified `openPageEditor` renders page cards with 1-tap delete, move buttons, and checkbox pills.
     - Verified page selection, Select All, Deselect All, and button disabled/enabled states.
     - Verified extract submodal category dropdown, custom category toggle, tenant pre-fill, and date pre-fill.
     - Verified extract API execution with correct JSON payload and new document opening.
     - Verified delete API execution with confirmation prompt.
   - **Result:** **444/444 Vitest tests passed across 37 test files** (0 failed).
