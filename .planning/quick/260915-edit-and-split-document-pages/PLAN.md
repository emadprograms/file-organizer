---
status: completed
quick_id: 260915-gpe
slug: edit-and-split-document-pages
date: 2026-09-15
description: Interactive document page editor, page separation, reordering, and deletion on computer and tablet
---

# Plan: Interactive Document Page Editor, Page Separation, Reordering, and Deletion

## User Intent
Enable users on both computer (desktop) and tab (tablet / touchscreens) to visually inspect and edit documents page-by-page. Specifically:
1. When multiple forms (e.g. Maintenance letter, Rent Deduction letter, Key Handover) are bundled together into one multi-page PDF document, allow separating/extracting specific pages into a new document and moving them to their rightful category (e.g. `04 - محضر تسليم مفتاح` or `07 - استقطاع إيجار`) and tenant.
2. Allow deleting individual pages (e.g. blank pages, duplicate scans) directly on tab with a simple 1-tap delete button or multi-select deletion, updating the physical PDF and database.
3. Allow reordering pages within a document on both desktop and tablet.
4. Ensure 100% database integrity across `documents`, `pages`, and `batches` tables with atomic transactions, preserving provenance and avoiding any orphaned records or constraint violations.

## Key Changes
1. Backend Models & DTOs (`src/HousingApplication.Web/Models/DTOs.cs`):
   - Add `ExtractPagesRequestDto`, `ExtractPagesResponseDto`, `DeletePagesRequestDto`, `DeletePagesResponseDto`, `ReorderPagesRequestDto`, `ReorderPagesResponseDto`.
2. Backend Repository & Service (`src/HousingApplication.Web/Data/IFileOrganizerRepository.cs` and `FileOrganizerRepository.cs`):
   - Implement `ExtractPagesAsync`:
     - Reads source PDF via `PdfSharpCore`.
     - Extracts requested page indices into new PDF (`doc_{newVaultId}.pdf`) in house vault.
     - Updates source PDF to retain remaining pages (or deletes source doc if all pages extracted).
     - Inserts new document record in `documents` with inherited `batch_id`, target category, tenant, title, date, `is_manual = 1`.
     - Reassigns extracted rows in `pages` table (`vault_id = newVaultId`, `category = targetCategory`, `tenant_id = targetTenantId`).
     - Re-indexes page numbers of remaining pages in source document.
   - Implement `DeletePagesAsync`:
     - Removes specified pages from physical PDF via `PdfSharpCore`.
     - Decrements `documents.page_count` (or deletes document if 0 pages left).
     - Removes/unlinks pages from `pages` table.
     - Decrements `batches.page_count` to maintain exact parity with surviving pages.
   - Implement `ReorderPagesAsync`:
     - Reconstructs physical PDF with new page order.
     - Updates `pages` table sequence.
3. Backend Endpoints (`src/HousingApplication.Web/Program.cs`):
   - `POST /api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/extract-pages`
   - `POST /api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/delete-pages`
   - `POST /api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/reorder-pages`
4. Frontend Components (`src/HousingApplication.Web/wwwroot/js/` & `index.html`):
   - Create `doc-page-editor.js`:
     - Thumbnail grid rendering using `lib/pdfjs`.
     - Touch-first responsive page cards with 1-tap delete `🗑️`, reorder buttons `◀ ▶`, and tap-to-select.
     - Sticky bottom toolbar with `Separate & Move...`, `Delete Selected`, `Select All / Deselect All`.
     - Sub-modal for `Separate & Move`: Category picker, Tenant picker, Arabic title, Date picker.
   - Update `index.html`:
     - Add `id="viewer-edit-pages-btn"` to document viewer header.
     - Add `doc-page-editor-modal` container with Tailwind CSS styling and dark mode support.
     - Include `<script src="js/doc-page-editor.js">`.
   - Update `doc-manager.js`:
     - Add `✂️ Edit & Split Pages` action to three-dots dropdown menu.
   - Update `pdf-preview.js`:
     - Add `✂️ Edit Pages` action to Document Inspector header.
   - Mirror updated web assets to `dist/win-x64/wwwroot/`.
5. Testing & Verification:
   - Add comprehensive backend unit tests in `tests/HousingApplication.Tests/` covering page extraction, deletion, reordering, and batch/foreign-key integrity.
   - Add frontend tests in `tests/web/components/doc_page_editor.test.js`.
   - Run complete test suite (`dotnet test` + `npm test`) ensuring 100% pass rate.
