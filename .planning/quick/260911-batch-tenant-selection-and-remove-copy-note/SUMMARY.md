# Quick Task Summary: Batch Tenant Selection & Remove Copy Note (QCK-08)

**Task ID**: `260911-batch-tenant-selection-and-remove-copy-note`  
**Milestone**: v14.0 Power-User Operations & Portfolio Expansion (QCK-08)  
**Status**: Completed  
**Date**: 2026-09-11  

## Overview
Implemented Quick Task `260911-batch-tenant-selection-and-remove-copy-note` (QCK-08) to provide granular tenancy control during multi-document batch operations and eliminate explanatory visual clutter:
1. Removed the verbose amber explanatory note (`💡 ملاحظة: النسخ يتيح ظهور الوثائق في مجلد إضافي للرجوع السريع دون تكرارها في الخط الزمني`) from the Batch Copy modal (`#batch-copy-modal`) without replacement, preserving modal clarity and intuitive UI principles.
2. Removed the pillar emoji (`🏛️`) and completely eliminated artificial options like "Keep current tenant" / "الاحتفاظ بالمستأجر الحالي".
3. Added Target Tenant dropdown selectors (`المستأجر • Target Tenant`) to both the Batch Move modal (`#batch-move-tenant-select`) and Batch Copy modal (`#batch-copy-tenant-select`), listing ONLY the actual tenants registered for that house (e.g., `خالد العتيبي (المستأجر الحالي)`, `محمد مبارك (2020 – 2022)`).
4. The tenant to whom the folder/document belongs is pre-selected by default. If the user wants to change it, they select another tenant from the dropdown.
5. Added robust Area and House resolution (`getBatchResolvedArea`, `getBatchResolvedHouse`) using memory variables and URL hash extraction to guarantee dependable tenant loading and batch API dispatch.
6. Cleaned confirm button labels to concise action text: `Move Documents` and `Copy Documents`.
7. Extended backend schemas, handlers, and repositories across FastAPI and ASP.NET Core 8.0 to support `target_tenant_id: Optional[int]`.
8. Maintained zero diff between `src/api/static/` and `web-net/wwwroot/` with 100% test pass rate across Vitest, Pytest, and xUnit.

---

## Changes Implemented

### 1. Frontend UI & Templates (`src/api/static/index.html`)
- In `#batch-copy-modal`:
  - Removed the entire amber note block (`<div class="p-3 bg-amber-50/80 border border-amber-200/80 rounded-xl text-amber-900 text-xs flex items-start gap-2">...</div>`).
  - Added `#batch-copy-tenant-select` dropdown populated dynamically with house tenants (no artificial placeholder options).
  - Updated confirm button text to `Copy Documents`.
- In `#batch-move-modal`:
  - Added `#batch-move-tenant-select` dropdown populated dynamically with house tenants (no artificial placeholder options).
  - Updated confirm button text to `Move Documents`.

### 2. Frontend Logic (`src/api/static/js/categories-view.js`)
- Implemented `populateBatchTenantSelect(selectId)`:
  - Eliminates `🏛️` pillar emoji, artificial placeholders, and distracting emojis (`🟢`, `👤`).
  - Formats options with clean Arabic indicators: `(المستأجر الحالي)` and date ranges `(YYYY – YYYY)`.
  - Analyzes selected documents via `getBatchSelectedDocsInfo()`.
  - Pre-selects the tenant to whom the folder/document belongs by default.
  - Lists only real house tenants; user changes selection directly if they want another tenant.
  - Fetches tenant records from `/api/areas/{area}/houses/{house}/tenants` resolved via `getBatchResolvedArea()` and `getBatchResolvedHouse()`.
  - Gracefully falls back to extracting unique non-null tenants from `currentCategories` if the network request fails or runs offline.
- Updated `openBatchMoveModal` and `openBatchCopyModal` to invoke `populateBatchTenantSelect`.
- Updated `handleBatchMoveSubmit`, `handleBatchCopySubmit`, and `handleBatchDeleteSubmit` to use `getBatchResolvedArea()` and `getBatchResolvedHouse()`:
  - If a valid tenant is chosen, injects `target_tenant_id: parseInt(targetTenantId, 10)` into the JSON request body.
  - If `""` (Keep current tenant) is chosen, omits `target_tenant_id`, maintaining original document tenancy.
- Exported `populateBatchTenantSelect`, `getBatchResolvedArea`, `getBatchResolvedHouse`, `formatBatchTenantLabel`, and `getBatchSelectedDocsInfo` on `window` and `module.exports` for testability.

### 3. FastAPI / Python Backend
- `src/api/models.py`:
  - Added `target_tenant_id: Optional[int] = None` to `BatchMoveRequest` and `BatchCopyRequest`.
- `src/api/routes.py`:
  - In `batch_move_documents`: If `req.target_tenant_id is not None`, updates `category = ?, tenant_id = ?, is_manual = 1`; otherwise updates `category = ?, is_manual = 1` preserving existing `tenant_id`.
  - In `batch_copy_documents_route`: Forwards `req.target_tenant_id` to `repo.batch_copy_documents`.
- `src/db/repository.py`:
  - Updated standalone function `batch_copy_documents` and `Repository.batch_copy_documents` to accept `target_tenant_id: Optional[int] = None`.
  - Computes `doc_tenant_id = target_tenant_id if target_tenant_id is not None else src.tenant_id`.
  - Copies preserve physical file paths on disk and set `is_timeline_visible = 0`.

### 4. ASP.NET Core 8.0 / C# Backend
- `web-net/Models/DTOs.cs`:
  - Added `[JsonPropertyName("target_tenant_id")] public int? TargetTenantId { get; init; }` to `BatchMoveRequestDto` and `BatchCopyRequestDto`.
- `web-net/Data/IFileOrganizerRepository.cs` & `web-net/Data/FileOrganizerRepository.cs`:
  - Updated `BatchMoveDocumentsAsync(..., int? targetTenantId = null)`: dynamically includes `tenant_id = @TargetTenantId` when supplied.
  - Updated `BatchCopyDocumentsAsync(..., int? targetTenantId = null)`: sets duplicate record's `tenant_id = targetTenantId ?? src.tenant_id`.
- `web-net/Program.cs`:
  - Passed `dto.TargetTenantId` into `BatchMoveDocumentsAsync` and `BatchCopyDocumentsAsync`.

### 5. Static Asset Parity
- Recompiled and synced assets via `~/.dotnet/dotnet build web-net/FileOrganizer.Web.csproj`.
- Verified 0 diff via `diff -ru src/api/static/ web-net/wwwroot/`.

---

## Verification & Test Results

1. **Frontend Vitest Component Tests (`npm run test:frontend`)**:
   - `tests/frontend/components/batch_operations.test.js`:
     - Verified `#batch-move-tenant-select` and `#batch-copy-tenant-select` elements exist in DOM.
     - Verified absence of amber copy note.
     - Verified `populateBatchTenantSelect` populates tenant options with active indicators and lease tags.
     - Verified fallback to `currentCategories` when API fetch fails.
     - Verified `handleBatchMoveSubmit` sends `target_tenant_id` when selected.
     - Verified `handleBatchCopySubmit` sends `target_tenant_id` when selected.
     - Verified omission of `target_tenant_id` when "Same Tenant" is selected.
   - Total: **113 passed** across 10 files (14 in `batch_operations.test.js`).

2. **Python Pytest Backend Tests (`.venv/bin/pytest tests/test_v14_features.py tests/test_document_management_api.py -v`)**:
   - `test_batch_move_with_target_tenant`: Verified moving documents reassigns `tenant_id` when specified, and preserves existing `tenant_id` when omitted.
   - `test_batch_copy_with_target_tenant`: Verified copying documents reassigns `tenant_id` when specified, and preserves existing `tenant_id` when omitted while maintaining `is_timeline_visible = 0`.
   - Total: **30 passed** (17 in `test_v14_features.py`, 13 in `test_document_management_api.py`).

3. **ASP.NET Core xUnit Tests (`~/.dotnet/dotnet test web-net/FileOrganizer.Tests/`)**:
   - `BatchMove_UpdatesDocuments_Returns200Ok`: Verified updating category and `TargetTenantId` in SQLite.
   - `BatchCopy_CreatesDocumentCopies_ExcludedFromTimeline`: Verified creating copies with `TargetTenantId` while excluding them from timeline queries.
   - Total: **84 passed** (0 failed, 0 skipped).
