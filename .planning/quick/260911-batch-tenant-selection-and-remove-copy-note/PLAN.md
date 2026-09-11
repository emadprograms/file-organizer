# Quick Task Plan: Batch Tenant Selection & Remove Copy Note (QCK-08)

**Task ID**: `260911-batch-tenant-selection-and-remove-copy-note`  
**Milestone**: v14.0 Power-User Operations & Portfolio Expansion (QCK-08)  
**Status**: Completed  
**Date**: 2026-09-11  

## Objective
Enhance batch operations in the digital archive management system by:
1. Removing the verbose, redundant amber explanatory note from the Batch Copy modal (`#batch-copy-modal`) without replacement, adhering to the platform's intuitive, minimal-text design philosophy.
2. Adding a Target Tenant selector (`المستأجر • Target Tenant`) to both the Batch Move modal (`#batch-move-tenant-select`) and Batch Copy modal (`#batch-copy-tenant-select`), defaulting to `🏛️ المستأجر الحالي للوثيقة • Same Tenant` (preserving existing document tenancy) while allowing users to move or copy documents across tenants within the house.
3. Polishing modal confirm button text to clean action verbs: `Move Documents` and `Copy Documents`.
4. Supporting `target_tenant_id` end-to-end across both FastAPI and ASP.NET Core 8.0 backends and database repository layers.
5. Maintaining 100% test coverage and 0 static diff between `src/api/static/` and `web-net/wwwroot/`.

---

## User Intent & Requirements

1. **Remove Copy Note (`#batch-copy-modal`)**:
   - Strip the amber callout block:
     `<div class="p-3 bg-amber-50/80 border border-amber-200/80 rounded-xl text-amber-900 text-xs flex items-start gap-2">...</div>`
   - Leave no replacement text or notice.

2. **Target Tenant Selection in Move & Copy Modals**:
   - In Move Selected modal (`#batch-move-modal`), insert Target Tenant dropdown above category folder selection:
     ```html
     <div>
         <label class="block text-xs font-bold text-slate-700 mb-1.5">المستأجر • Target Tenant</label>
         <select id="batch-move-tenant-select" class="w-full px-3 py-2 text-xs border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none bg-slate-50 focus:bg-white font-medium">
             <option value="">🏛️ المستأجر الحالي للوثيقة • Same Tenant</option>
         </select>
     </div>
     ```
   - In Copy Selected modal (`#batch-copy-modal`), insert Target Tenant dropdown above category folder selection:
     ```html
     <div>
         <label class="block text-xs font-bold text-slate-700 mb-1.5">المستأجر • Target Tenant</label>
         <select id="batch-copy-tenant-select" class="w-full px-3 py-2 text-xs border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-slate-50 focus:bg-white font-medium">
             <option value="">🏛️ المستأجر الحالي للوثيقة • Same Tenant</option>
         </select>
     </div>
     ```
   - Update confirm button labels to clean phrasing:
     - `#batch-move-btn-text`: `Move Documents`
     - `#batch-copy-btn-text`: `Copy Documents`

3. **Dynamic Tenant Population & Fallback (`categories-view.js`)**:
   - Implement `populateBatchTenantSelect(selectId)`:
     - Clear existing dynamic options, retaining default option `🏛️ المستأجر الحالي للوثيقة • Same Tenant` (value `""`).
     - Fetch active house tenants via `/api/areas/{area}/houses/{house}/tenants`.
     - Render options indicating status (`🟢 ` for active, `👤 ` for past) and lease years (`[YYYY - YYYY]`).
     - Fallback gracefully to distinct non-null tenants in `currentCategories` if offline or API is unavailable.
   - Invoke `populateBatchTenantSelect` inside `openBatchMoveModal` and `openBatchCopyModal`.
   - Update `handleBatchMoveSubmit` and `handleBatchCopySubmit` to read the selected tenant:
     - If non-empty, parse integer and include `target_tenant_id: parseInt(targetTenantId, 10)` in payload.
     - If empty, omit `target_tenant_id` (or pass `null`), preserving each document's existing tenant ID.

4. **Dual-Backend Parity (FastAPI & ASP.NET Core 8.0)**:
   - **FastAPI / Python**:
     - `src/api/models.py`: Add `target_tenant_id: Optional[int] = None` to `BatchMoveRequest` and `BatchCopyRequest`.
     - `src/api/routes.py`:
       - `batch_move_documents`: If `req.target_tenant_id is not None`, update `category = ?, tenant_id = ?, is_manual = 1`; else preserve `tenant_id`.
       - `batch_copy_documents_route`: Pass `req.target_tenant_id` to repository function.
     - `src/db/repository.py`:
       - `batch_copy_documents`: Set duplicate document's `tenant_id = target_tenant_id if target_tenant_id is not None else src.tenant_id`.
   - **ASP.NET Core 8.0 / C#**:
     - `web-net/Models/DTOs.cs`: Add `[JsonPropertyName("target_tenant_id")] public int? TargetTenantId { get; init; }` to `BatchMoveRequestDto` and `BatchCopyRequestDto`.
     - `web-net/Data/IFileOrganizerRepository.cs` & `FileOrganizerRepository.cs`: Update `BatchMoveDocumentsAsync` and `BatchCopyDocumentsAsync` signatures and implementations to accept `int? targetTenantId = null`.
     - `web-net/Program.cs`: Pass `dto.TargetTenantId` to both repository methods.

5. **Testing & Verification**:
   - Vitest component tests: verify DOM setup, note removal, dropdown population, and payload propagation.
   - Pytest tests: test batch move and copy with explicit `target_tenant_id` and default preservation.
   - xUnit tests: test batch move and copy with explicit `TargetTenantId` and default preservation in C#.
   - Static asset verification: verify 0 diff between `src/api/static/` and `web-net/wwwroot/`.
