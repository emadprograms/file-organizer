---
status: investigating
trigger: "the code has regressed when moving documents by default it would show the same tenant's name. now it shows the current tenant's name by default."
created: 2026-09-17
updated: 2026-09-17
---

## Current Focus
- hypothesis: "In categories-view.js:getBatchSelectedDocsInfo, openTenant (resolving to currentTenant/resident tenant) is given Priority 1 over the document's own tenant (singleTargetDoc.tenant / tenantNames / tenantIds), causing the Move and Copy modals to pre-select the current tenant instead of the document's own tenant."
- next_action: "Confirm understanding with user, reverse priority in getBatchSelectedDocsInfo so the document's own tenant takes priority over currentTenant, update multi-stack assets, add Vitest tests, and verify."

## Symptoms
- **Expected behavior**: When moving or copying a document, the tenant dropdown in the move modal should default to the same tenant that currently owns the document.
- **Actual behavior**: It defaults to the house's current/resident tenant (`المستأجر الحالي`) instead of the document's own tenant.
- **Timeline**: Regressed after changes to `getBatchSelectedDocsInfo` introduced `openTenant` priority ahead of document tenant resolution.
- **Reproduction**:
  1. Open a house with multiple tenants (e.g. current resident and previous tenant).
  2. Click the 3-dot menu on a document belonging to the previous tenant and select "Move".
  3. The Move modal opens and `#batch-move-tenant-select` pre-selects the house's current resident tenant instead of the document's own tenant.

## Root Cause
In `src/HousingApplication.Web/wwwroot/js/categories-view.js`:
Because `getBatchResolvedTenant()` resolves `currentTenant` (the active resident tenant of the house), `targetTenantName` was always set to `currentTenant` under Priority 1. As a result, the fallback for `singleTargetDoc` and `selectedDocIds` was never reached whenever `currentTenant` was defined.
