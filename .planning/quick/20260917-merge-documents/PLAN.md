# Quick Plan: Merge Documents Feature

**User Request:** "just like we ahve the feature to split documents. add the feature to merge docuemnts as well. two different documents should be allowed to be merged as well."

## Goal
Implement a complete end-to-end document merge feature that allows users to merge two (or more) documents into a single PDF document with custom page ordering, target category, tenant, title, date, and optional deletion of the original source documents.

## Architecture & Implementation Plan

### 1. Backend (C# / ASP.NET Core & PdfSharpCore)
- **DTOs (`src/HousingApplication.Web/Models/DTOs.cs`)**:
  - `MergeDocumentsRequestDto`: `vault_ids`, `target_title`, `target_category`, `target_tenant_id`, `target_date`, `target_notes`, `delete_sources`.
  - `MergeDocumentsResponseDto`: `status`, `merged_vault_id`, `merged_category`, `merged_tenant_id`, `merged_tenant_name`, `merged_title`, `total_pages`, `source_vault_ids`, `sources_deleted`.
- **Repository Interface & Implementation (`IFileOrganizerRepository.cs` & `FileOrganizerRepository.cs`)**:
  - `Task<MergeDocumentsResponseDto> MergeDocumentsAsync(string areaId, string houseId, MergeDocumentsRequestDto request, string? areasRoot = null)`
  - Validates `VaultIds.Count >= 2`.
  - Retrieves documents metadata from SQLite in the specified order.
  - Combines physical PDF pages in the ordered sequence using `PdfSharpCore`.
  - Generates `newVaultId`, writes merged PDF to `vault/doc_{newVaultId}.pdf`.
  - Inserts new document record into `documents` table and page records into `pages` table.
  - If `delete_sources == true`, deletes source documents from `documents` and `pages` tables, and deletes their physical files safely.
- **API Endpoints (`src/HousingApplication.Web/Program.cs`)**:
  - `POST /api/areas/{areaId}/houses/{houseId}/documents/merge`
  - `POST /api/documents/merge`

### 2. Frontend (HTML & JavaScript)
- **Modal Markup (`src/HousingApplication.Web/wwwroot/index.html`)**:
  - `#merge-docs-modal`: Modal dialog with document order list (reordering controls `▲`/`▼`), document picker to select second document, title, category, tenant, date, notes, and `delete_sources` checkbox.
  - `#btn-batch-merge`: Added to floating `#batch-action-bar` for instant merge when 2+ documents are selected in categories view.
  - `#viewer-merge-btn`: Added to document viewer top toolbar next to `#viewer-edit-pages-btn`.
  - `#btn-doc-merge`: Added to manage document modal footer.
- **Categories View & Batch Bar (`src/HousingApplication.Web/wwwroot/js/categories-view.js`)**:
  - Wire `#btn-batch-merge` in `initBatchOperations` and update `#btn-batch-merge` state in `updateBatchActionBar` (enabled when >= 2 docs selected).
- **Document Manager (`src/HousingApplication.Web/wwwroot/js/doc-manager.js`)**:
  - Add `🔗 Merge Document` (`.doc-menu-item-merge`) to 3-dots dropdown menu.
  - Implement `openMergeModal(initialDocs, fallbackCategory)` and helper functions:
    - Reorder documents in list.
    - Pick second document from house documents.
    - Submit merge request to API.
    - Handle success toast, UI refresh, and open merged document.
- **Document Viewer (`src/HousingApplication.Web/wwwroot/js/doc-viewer.js`)**:
  - Wire `#viewer-merge-btn` to call `window.openMergeModal([currentPinnedDoc])`.
- **Sync Distribution Files**:
  - Copy updated HTML and JS files to `dist/win-x64/wwwroot/`.

### 3. Testing
- Backend unit / integration tests in `tests/HousingApplication.Tests/ApiEndpointTests.cs` or dedicated `tests/HousingApplication.Tests/MergeDocumentsTests.cs`.
- Frontend Vitest tests in `tests/web/components/merge_documents.test.js`.
- Run all test suites to ensure zero regressions.
