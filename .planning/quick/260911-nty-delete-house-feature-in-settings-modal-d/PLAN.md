# Quick Task 260911-nty: Delete House Feature in Settings Modal Danger Zone

**Task:** Delete House Feature in House Settings Modal (`#tenant-modal`) with Danger Zone, GitHub-Style Type-to-Confirm Modal, Dual-Backend Cascade Deletion, and Frontend State Cleanup
**Mode:** quick
**Date:** 2026-09-11

## Must Haves

1. **Backend Endpoints & Cascade Deletion:**
   - ASP.NET Core: `DELETE /api/areas/{areaId}/houses/{houseId}` cascades removal of pages, documents, batches, tenants, houses in SQLite and deletes directory from disk (`areas/{area}/{house}`).
   - Python FastAPI: `DELETE /api/areas/{area_id}/houses/{house_id}` with identical cascade database and filesystem removal.
2. **Frontend Danger Zone in House Settings (`#tenant-modal`):**
   - Distinct red card container at the bottom of the modal with warning text and `#btn-open-delete-house` trigger button.
3. **GitHub-Style Type-to-Confirm Modal (`#delete-house-modal`):**
   - Displays target house name and warning callout.
   - Text input `#delete-house-confirm-input` requiring exact confirmation text `delete <house_id>` to enable the confirmation button.
   - Loading spinner state during async deletion call.
4. **State Transition & UI Refresh:**
   - On successful deletion, resets `currentHouse = null`, `currentTenant = null`, navigates back to Area Grid, refreshes the sidebar tree, re-renders the area grid, and displays a success toast.
5. **Multi-Stack Tests & Parity:**
   - Vitest unit tests for modal interactions, type-to-confirm validation, and state cleanup.
   - .NET xUnit and Python pytest backend tests verifying cascade DB deletion and disk cleanup.
   - Exact parity (`0 static asset diff`) between `src/api/static` and `web-net/wwwroot`.
