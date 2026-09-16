---
status: resolved
trigger: "the edit pages button works but everything inside it is almost broken. move and replace does nothing. the top header says no tenant. i don't know and cannot check if it is properly linked to the database and won't break anything. please check so if these things. and make proper tests. you didn't make proper tests for these that is causing this issue."
created: 2026-09-16
updated: 2026-09-16
---

## Root Causes Identified
1. **Header 'No Tenant' Display**:
   - `doc-viewer.js` only passed `{ vault_id, title, category, area_id, house_id }` without tenant information to `openPageEditor()`.
   - `doc-page-editor.js` fell back to `'No Tenant'` in English instead of resolving authoritative document metadata and resident tenant from SQLite.
2. **Move & Replace / Separate & Move and Reordering Failures**:
   - When opened from the document viewer or routes where `currentArea` or `currentHouse` defaulted to `'default'`, `ExtractPagesAsync`, `DeletePagesAsync`, and `ReorderPagesAsync` were searching for physical PDF files under `../areas/default/default/vault/`, resulting in 404 / file not found errors.
   - When extracting new documents, `house_id` was being assigned as `'default'` instead of resolving the source document's true house ID from SQLite (`houses h ON d.house_id = h.id`), risking foreign key constraint violations and orphan records.
   - In `shiftPageOrder()`, clicking `◀` or `▶` repeatedly caused local state desynchronization because `currentPageOrder` was not reset to `1..N` after physical rewriting of the PDF file on disk, and `activePdfDoc` in pdf.js memory was never reloaded with cache-busting timestamps. The document viewer iframe also never received a reload command to bust its cache.

## Key Changes
1. **Authoritative DB Metadata & Robust Route Handling**:
   - Added universal endpoint `app.MapGet("/api/documents/{vaultId}/metadata")` in `Program.cs` returning full `DocumentDetailsDto` with `TenantName`, `TenantId`, `AreaId`, `HouseId`, `Category`, `ArabicTitle`, `PageCount`.
   - Updated `openPageEditor()` in `doc-page-editor.js` to asynchronously fetch authoritative metadata directly from SQLite. Subtitle now renders the resident tenant's name, or Arabic `"كامل المنزل (عام)"` if unassigned. Never renders English `"No Tenant"`.
   - In `FileOrganizerRepository.cs`, `ExtractPagesAsync`, `DeletePagesAsync`, and `ReorderPagesAsync` now query `d.house_id AS HouseId, d.tenant_id AS TenantId, h.area_id AS AreaId` from SQLite. Even if the client passes `"default"` in the URL, the repository derives the true `AreaId` and `HouseId` from the database.
   - Added foreign key safeguard in `ExtractPagesAsync`: if `targetTenantId <= 0`, it resolves resident tenant, any house tenant, or creates a fallback default tenant, ensuring zero foreign key constraint violations in SQLite.
2. **Reordering & Cache-Busting Synchronization**:
   - Added `isReordering` lock to prevent double-click / rapid touch events on tablets.
   - Reset `currentPageOrder = [1..N]` upon successful persistence so subsequent reorder operations apply relative to the newly rewritten file on disk.
   - Added cache-busting timestamping to reload `activePdfDoc` in `doc-page-editor.js` and reload the viewer panel via `window.reloadCurrentDocument(true)`.
3. **Separate & Move Tenant Options**:
   - Added `"كامل المنزل (عام) • General House Document"` option in the extract modal.
   - Pre-selects resident tenant or general house document appropriately.
4. **Exhaustive Testing**:
   - **Backend (`tests/HousingApplication.Tests/RepositoryTests.cs` and `ApiEndpointTests.cs`)**:
     - `ExtractPagesAsync_WithDefaultAreaAndHouseInUrl_ResolvesRealAreaAndHouseFromDatabase`
     - `ReorderPagesAsync_WithDefaultAreaAndHouseInUrl_ResolvesRealAreaAndHouseFromDatabase`
     - `ExtractPagesAsync_WithTargetTenantZeroOrNull_SafelyResolvesTenantWithoutForeignConstraintViolation`
     - `GetDocumentMetadata_DirectVaultEndpoint_ReturnsMetadataWithTenantAndAreaInfo`
     - `GetDocumentMetadata_NonExistentVaultId_ReturnsNotFound`
     - `ExtractPages_ApiEndpoint_WithDefaultAreaAndHouseInUrl_SucceedsByResolvingRealHouseFromDatabase`
     - Full test run: **951 passed, 0 failed**.
   - **Frontend (`tests/web/components/doc_page_editor.test.js`)**:
     - Subtitle displays real tenant from SQLite metadata.
     - Subtitle displays `"كامل المنزل (عام)"` when unassigned, never `"No Tenant"`.
     - Populates general house document option and pre-selects resident tenant.
     - Reorders pages and resets local order sequence with cache-busted reload.
     - Full test run: **37 test files, 454 passed, 0 failed**.
