---
status: complete
date: 2026-09-11
task_id: 260911-nty
---

# Quick Task Summary: Delete House Feature in Settings Modal Danger Zone

## Overview
Implemented the **Delete House** feature inside the House Settings & Tenants modal (`#tenant-modal`) with a dedicated "Danger Zone", a GitHub-style type-to-confirm modal dialog (`#delete-house-modal`), dual-backend cascade deletion endpoints (ASP.NET Core 8.0 Minimal APIs & FastAPI), disk directory removal (`areas/{area}/{house}`), and frontend state/UI reset with automated refresh.

## Key Changes
1. **ASP.NET Core 8.0 Backend (`web-net/`):**
   - Added `Task<bool> DeleteHouseAsync(string areaId, string houseId, string? areasRoot = null)` to `IFileOrganizerRepository` and `FileOrganizerRepository`.
   - Performed SQLite transaction cascade: deletes associated records from `pages`, `documents`, `batches`, `tenants`, and `houses`.
   - Cleaned up physical house directory (`areas/{area}/{house}`) on disk recursively.
   - Mapped `DELETE /api/areas/{areaId}/houses/{houseId}` in `Program.cs`.
   - Added comprehensive integration test `DeleteHouse_CascadeDeletesRecordsAndDirectory_ReturnsOk` in `FileOrganizer.Tests/ApiEndpointTests.cs` (85/85 xUnit tests passing).
2. **FastAPI Python Backend (`src/`):**
   - Added `delete_house(conn, house_id, area_id, areas_root, autocommit=True) -> bool` to `src/db/repository.py` and wrapped in `Repository.delete_house`.
   - Implemented `@router.delete("/api/areas/{area_id}/houses/{house_id}")` in `src/api/routes.py`.
   - Added test `test_delete_house_endpoint` in `tests/test_v14_features.py` (18/18 pytest tests passing).
3. **Frontend UI & Safety UX:**
   - Added a red-themed **Danger Zone / منطقة الخطر** container inside `#tenant-modal` with button `#btn-open-delete-house` ("حذف المنزل / Delete House").
   - Added GitHub-style confirmation modal `#delete-house-modal`:
     - Displays house name and warning callouts regarding permanent removal from both database and disk.
     - Requires the user to type `delete <house_id>` into `#delete-house-confirm-input` before the confirmation button `#delete-house-confirm-btn` enables.
     - Provides loading spinner feedback during asynchronous deletion.
   - Updated `tenant-manager.js`:
     - Dispatches `DELETE /api/areas/{areaId}/houses/{houseId}`.
     - Resets active state: `currentHouse = null`, `currentTenant = null`.
     - Automatically transitions view back to the Area Grid (`#area-grid-panel`).
     - Refreshes sidebar tree (`window.loadTree()`) and Area Grid cards (`window.selectAreaGrid()`).
     - Displays confirmation toast: `showToast("تم حذف المنزل بنجاح / House deleted successfully", "success")`.
4. **Parity & Testing:**
   - Synchronized assets across `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/` with zero static diff.
   - Added 5 new Vitest unit tests in `tests/frontend/components/delete_house.test.js` (157 Vitest tests across 16 files passing).
