---
status: resolved
trigger: "the code has regressed when moving documents by default it would show the same tenant's name. now it shows the current tenant's name by default."
created: 2026-09-17
updated: 2026-09-17
---

## Current Focus
- hypothesis: "In categories-view.js:getBatchSelectedDocsInfo, openTenant (resolving to currentTenant/resident tenant) was given Priority 1 over the document's own tenant (singleTargetDoc.tenant / tenantNames / tenantIds), causing the Move and Copy modals to pre-select the current tenant instead of the document's own tenant."
- resolution: "Reversed priority in getBatchSelectedDocsInfo so the document's own tenant takes Priority 1 (singleTargetDoc) and Priority 2 (selected documents), falling back to open/currentTenant only if no document tenant is defined. Fixed isMovingToOtherTenant comparison and deduplicated combined tenants by both ID and Name. Verified across all 521 Vitest and 956 .NET tests."

## Symptoms
- **Expected behavior**: When moving or copying a document, the tenant dropdown in the move modal should default to the same tenant that currently owns the document.
- **Actual behavior**: It defaulted to the house's current/resident tenant (`المستأجر الحالي`) instead of the document's own tenant.
- **Timeline**: Regressed after changes to `getBatchSelectedDocsInfo` introduced `openTenant` priority ahead of document tenant resolution.
- **Reproduction**:
  1. Open a house with multiple tenants (e.g. current resident and previous tenant).
  2. Click the 3-dot menu on a document belonging to the previous tenant and select "Move".
  3. The Move modal opened and `#batch-move-tenant-select` pre-selected the house's current resident tenant instead of the document's own tenant.

## Root Cause
In `src/HousingApplication.Web/wwwroot/js/categories-view.js`:
Because `getBatchResolvedTenant()` resolves `currentTenant` (the active resident tenant of the house), `targetTenantName` was always set to `currentTenant` under Priority 1. As a result, the fallback for `singleTargetDoc` and `selectedDocIds` was never reached whenever `currentTenant` was defined.

## Fix
1. `getBatchSelectedDocsInfo()` in `src/HousingApplication.Web/wwwroot/js/categories-view.js` and `dist/win-x64/wwwroot/js/categories-view.js`:
   - Priority 1: `singleTargetDoc`'s own tenant (`tenant` / `primary_tenant` / `tenant_id` or matched category tenant).
   - Priority 2: Selected documents' own tenant from `selectedDocIds`.
   - Priority 3 (Fallback): `openTenant` from `getBatchResolvedTenant()`.
2. `populateBatchTenantSelect`:
   - Deduplicate combined tenants from DB and in-memory categories by both ID and Name to avoid duplicate `<option>` entries.
3. `isMovingToOtherTenant`:
   - Returns `false` immediately when `sourceTenantId === targetTenantVal`, correctly preserving tenancy when moving between categories under the same past tenant.
4. Vitest test coverage:
   - Added 3 test cases in `tests/web/components/move_to_other_tenant.test.js` covering single doc move, batch move, and unassigned fallback.
   - Updated `tests/web/components/batch_operations.test.js` to assert document's own tenant pre-selection.
