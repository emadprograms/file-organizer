# Quick Task Summary: 260910-delete-document-feature

## Overview
Added complete document deletion support across the entire stack:
1. **Frontend UI**: Added a red accent "Delete Document" button (`#btn-doc-delete`) inside the 3-dots document action modal (`#doc-action-modal`), with user confirmation dialog, loading feedback, error rendering, success toast, and live view/tree refreshing.
2. **Python FastAPI Backend**: Implemented `delete_document` in `src/db/repository.py` and `DELETE /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}` in `src/api/routes.py`, deleting physical vault files and cascading DB records (`pages` and `documents`).
3. **.NET ASP.NET Core Backend**: Implemented `DeleteDocumentAsync` in `web-net/Data/IFileOrganizerRepository.cs` and `web-net/Data/FileOrganizerRepository.cs`, and mapped `DELETE /api/areas/{areaId}/houses/{houseId}/documents/{vaultId}` in `web-net/Program.cs`.
4. **Asset Synchronization**: Rebuilt `web-net/FileOrganizer.Web.csproj` to automatically sync frontend static assets to `web-net/wwwroot/`.

---

## Key Changes

### 1. Python Backend
- `src/db/repository.py`:
  - Added `delete_document(conn, vault_id, house_id, area_id, areas_root, autocommit=True)` and method `Repository.delete_document(...)`.
  - Removes physical PDF files in `{areas_root}/{area_id}/{house_id}/vault/` (`doc_{vault_id}.pdf` / `{vault_id}.pdf`).
  - Executes `DELETE FROM pages WHERE vault_id = ?` and `DELETE FROM documents WHERE vault_id = ?`.
- `src/api/routes.py`:
  - Added endpoint `DELETE /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}`.
  - Returns `200 OK` with `{"status": "success", "message": f"Document {vault_id} deleted"}` or raises `HTTPException(404)`.
  - Calls `clear_tree_cache()` upon successful deletion.

### 2. .NET ASP.NET Core Backend Parity
- `web-net/Data/IFileOrganizerRepository.cs`:
  - Added `Task<bool> DeleteDocumentAsync(string areaId, string houseId, string vaultId, string? areasRoot = null);`.
- `web-net/Data/FileOrganizerRepository.cs`:
  - Implemented `DeleteDocumentAsync` resolving physical file candidates from `{areasRoot}/{areaId}/{houseId}/vault/` and deleting them safely.
  - Executed atomic transaction removing related `pages` and `documents` rows.
- `web-net/Program.cs`:
  - Mapped `app.MapDelete("/api/areas/{areaId}/houses/{houseId}/documents/{vaultId}", ...)` returning `200 OK` or `404 NotFound`.

### 3. Frontend UI
- `src/api/static/index.html`:
  - Added `#btn-doc-delete` with red accent, left-aligned (`mr-auto`) in the `#doc-action-modal` footer.
- `src/api/static/js/doc-manager.js`:
  - Added `handleDeleteDoc()` with confirmation prompt: `"Are you sure you want to permanently delete this document? This will remove the file and all its records."`.
  - Disables button and shows `"Deleting..."` state during API call.
  - Dispatches `DELETE` request, displays success toast `"Document deleted successfully."`, closes the modal, and triggers `refreshCurrentTab` and `loadTree`.
  - Displays any server error message in `#doc-modal-status`.
- Rebuilt `web-net/FileOrganizer.Web.csproj` to sync `index.html` and `doc-manager.js` to `web-net/wwwroot/`.

---

## Verification & Test Results

1. **Python API Tests**:
   - `tests/test_document_management_api.py`: Added `test_delete_document_success` and `test_delete_document_not_found`.
   - Result: 13 passed in 1.10s.
2. **.NET Tests**:
   - `web-net/FileOrganizer.Tests/RepositoryTests.cs`: Added `DeleteDocumentAsync_DeletesFileAndDatabaseRecords`.
   - `web-net/FileOrganizer.Tests/ApiEndpointTests.cs`: Added `DeleteDocument_Existing_Returns200Ok` and `DeleteDocument_NonExistent_Returns404NotFound`.
   - Result: 43 passed in 257ms.
3. **Frontend Component Tests (Vitest)**:
   - `tests/frontend/components/doc_manager.test.js`: Verified confirmation rejection, successful deletion flow, and error state display.
   - Result: 63 passed across 4 test files in 810ms.
4. **Playwright E2E Tests**:
   - `tests/frontend/test_ingest_batch_playwright.py`:
   - Result: 7 passed in 13.25s.
