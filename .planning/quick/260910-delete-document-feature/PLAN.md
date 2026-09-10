# Quick Task: Add Document Deletion Feature (API + UI + Tests)

## Context & Motivation
The user noted that when clicking the three-dots menu on a document, they can move or copy the document, but there is no option to delete it:
> "okay there is no option to delete the file. when I click on the three dots. I can move the file, copy it but I cannot delete it."

Currently, neither the frontend modal nor the backend API (Python FastAPI and .NET ASP.NET Core) has a document deletion implementation.

## Objectives & Deliverables
1. **Python Backend**:
   - Add `delete_document(vault_id, house_id, area_id, areas_root)` to `Repository` (`src/db/repository.py`).
     - Deletes the physical file `{areas_root}/{area_id}/{house_id}/vault/doc_{vault_id}.pdf`.
     - Deletes associated records from `pages` and `documents` tables.
   - Add `DELETE /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}` endpoint in `src/api/routes.py`.
2. **.NET Backend Parity**:
   - Add `DeleteDocumentAsync(areaId, houseId, vaultId)` in `web-net/Data/IFileOrganizerRepository.cs` and `web-net/Data/FileOrganizerRepository.cs`.
   - Map `DELETE /api/areas/{areaId}/houses/{houseId}/documents/{vaultId}` in `web-net/Program.cs`.
3. **Frontend UI**:
   - In `src/api/static/index.html`, add a prominent Delete button (`#btn-doc-delete`) inside `#doc-action-modal` footer (left-aligned in red).
   - In `src/api/static/js/doc-manager.js`, handle `#btn-doc-delete`:
     - Ask for user confirmation.
     - Call `DELETE /api/areas/{area}/houses/{house}/documents/{vault_id}`.
     - Show toast notification upon success.
     - Close modal and refresh active view (`window.refreshCurrentTab`) and tree.
4. **Automated Testing**:
   - Python test in `tests/test_document_management_api.py`.
   - .NET unit test in `web-net/FileOrganizer.Tests/RepositoryTests.cs`.
   - Frontend Vitest test verifying modal delete button behavior.
   - Playwright E2E browser test verifying end-to-end document deletion.
