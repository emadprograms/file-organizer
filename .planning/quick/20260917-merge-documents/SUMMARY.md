# Quick Task Summary: Merge Documents Feature

**Task:** Document Merge Capability (Split & Merge Parity)
**Execution Date:** 2026-09-17
**Status:** Completed

---

## 1. Overview & Goal
Just as the application has an extensive split & page editor feature (`doc-page-editor.js`), this quick task added document merging capabilities across the full stack. Users can now merge two or more documents into a single PDF document in custom page order, selecting the target title, category folder, tenant assignment, primary document date, and notes, with an option to either replace the original source documents or keep them intact as copies.

---

## 2. Key Changes Implemented

### Backend (C# & ASP.NET Core & PdfSharpCore)
- **DTOs (`src/HousingApplication.Web/Models/DTOs.cs`)**:
  - Added `MergeDocumentsRequestDto` with fields: `vault_ids` (`List<string>`), `target_title`, `target_category`, `target_tenant_id`, `target_date`, `target_notes`, `delete_sources` (`bool`).
  - Added `MergeDocumentsResponseDto` with fields: `status`, `merged_vault_id`, `merged_category`, `merged_tenant_id`, `merged_tenant_name`, `merged_title`, `total_pages`, `source_vault_ids`, `sources_deleted`.
- **Repository Interface & Implementation (`IFileOrganizerRepository.cs` & `FileOrganizerRepository.cs`)**:
  - Added `Task<MergeDocumentsResponseDto> MergeDocumentsAsync(...)`.
  - Validates that at least two documents are provided.
  - Opens each physical PDF in the user-specified sequence using `PdfSharpCore.Pdf.IO.PdfReader.Open(stream, PdfDocumentOpenMode.Import)`.
  - Appends each page in order into a new `PdfSharpCore.Pdf.PdfDocument`.
  - Writes the merged physical PDF to `vault/doc_{newVaultId}.pdf`.
  - Inserts new document row into SQLite `documents` table.
  - If `delete_sources == true`: reassigns existing page records in `pages` table to preserve foreign key constraints without collision, then removes source document rows and safely deletes their PDF files.
  - If `delete_sources == false`: marks new document with `is_manual = 1` and preserves original source documents and page mappings.
- **REST API Endpoints (`src/HousingApplication.Web/Program.cs`)**:
  - `POST /api/areas/{areaId}/houses/{houseId}/documents/merge`
  - `POST /api/documents/merge`
- **Unit Tests (`tests/HousingApplication.Tests/RepositoryTests.cs`)**:
  - Added 4 tests verifying valid merging, source deletion, input validation (< 2 docs throws `ArgumentException`), and physical PDF merging with `PdfSharpCore`. All tests passing.

### Frontend UI & User Interaction
- **Modal HTML (`src/HousingApplication.Web/wwwroot/index.html`)**:
  - Created `#merge-docs-modal` with dark mode support, emerald accents, and responsive layout.
  - Interactive document sequence list (`#merge-docs-list`) with `▲` and `▼` reordering buttons, document index tags, titles, category badges, tenant badges, page counts, and remove `✕` buttons.
  - Add document row (`#merge-add-doc-select` and `#btn-merge-add-doc`) for adding any other house document to the merge sequence.
  - Target fields: Title, Category folder (with custom folder support), Tenant selector, Document date, Notes, and Delete sources checkbox.
  - Real-time page count badge (`#merge-docs-count-badge`).
  - Added `#btn-batch-merge` in the floating bottom action bar (`#batch-action-bar`).
  - Added `#viewer-merge-btn` in the document viewer header toolbar.
  - Added `#btn-doc-merge` in the single-document action modal (`#doc-action-modal`).
- **Categories View Integration (`src/HousingApplication.Web/wwwroot/js/categories-view.js`)**:
  - Wired `#btn-batch-merge` to enable when `>= 2` documents are selected.
  - Implemented `openBatchMergeModal()` which gathers selected documents in order and triggers the merge modal.
- **Document Manager Integration (`src/HousingApplication.Web/wwwroot/js/doc-manager.js`)**:
  - Added `🔗 Merge Document` (`.doc-menu-item-merge`) to 3-dots action dropdown.
  - Implemented `openMergeModal`, `closeMergeModal`, `renderMergeDocsList`, `moveMergeDocUp`, `moveMergeDocDown`, `removeMergeDoc`, `handleAddDocToMergeList`, and `handleMergeDocsSubmit`.
  - Refreshes categories and tree views, and opens the newly merged document in the viewer.
- **Document Viewer Integration (`src/HousingApplication.Web/wwwroot/js/doc-viewer.js`)**:
  - Wired `#viewer-merge-btn` to initiate merging for the currently viewed document.
- **Distribution Sync**:
  - Synchronized updated files to `dist/win-x64/wwwroot/`.

---

## 3. Verification & Test Results
- **Backend .NET Tests**:
  - `dotnet test --filter MergeDocumentsAsync`: 4 / 4 passed.
- **Frontend Vitest Tests**:
  - `tests/web/components/merge_documents.test.js`: 12 / 12 passed.
  - Regression tests (`batch_operations.test.js`, `doc_manager.test.js`, `doc_viewer.test.js`): 85 / 85 passed.
