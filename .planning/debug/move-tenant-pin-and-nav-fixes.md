---
status: resolved
trigger: "when selecting the move document option by default the tenant whose folder you are in, his name should appear. when I click on the 3 dots or multi-select it sometimes shows random, sometimes latest tenant. No. the name of the tenant should be the one that is open. second of all, the lock pin. there is no way to unlock the documents and reset to auto. suppose user drageed the wrong files and later wants to change the tenant dates. reconclication won't work on those locked (or pinned) files. there should be way to unlock them. add this to the 3 dots for documents that are pinned. Unpin or pin both. suppose the document is in the correct place and the user wants to pin it. He can it pin it from the 3 dots too. and when in categories there is show in timeline option when clicking on 3 dots. when in the timeline. clicking on 3 dots should give a show in categories options. fix these. update milestone docs. make tests. commit and push changes."
created: 2026-09-12
updated: 2026-09-12
---

## Symptoms
1. **Move Document Tenant Pre-selection**: When opening the Move Document modal (either via 3 dots on a single document or via batch multi-select), the tenant dropdown (`#batch-move-tenant-select`) did not reliably select the tenant whose folder was currently open. Instead, it preserved stale previous selections (`prevVal`), picked random entries from `selectedDocIds` Set iteration order, or fell back to the latest active tenant from the database query's `ORDER BY`.
2. **Lock / Pin Toggle**: There was no option in the 3-dots action menu to unpin/unlock documents (`is_manual = 0`) so they could participate in auto-reconciliation when tenant dates were adjusted, nor to manually pin unpinned documents (`is_manual = 1`).
3. **Timeline-to-Categories Navigation**: While Categories view provided a "Show in Timeline" option in the 3-dots menu, the 3-dots menu in Timeline view still displayed "Show in Timeline" instead of switching to "Show in Categories".

## Root Causes
1. **Move Tenant Default**:
   - `renderTenantOptions` in `categories-view.js` was prioritizing `prevVal = select.value` over `matchedOption`. Stale values from previous moves persisted.
   - In `getBatchSelectedDocsInfo()`, `Array.from(tenantNames)[0]` took precedence over `activeTenant`, and `singleTargetDoc` was ignored when building `tenantIds` / `tenantNames`.
   - If `matchedOption` was null, `select.options[0]` was selected, which was the latest tenant due to DB `ORDER BY ... DESC`.
2. **Pin / Unpin in 3-Dots**:
   - The floating dropdown menu in `doc-manager.js` did not expose pin/unpin toggles.
   - Backend .NET `ResetDocumentLockAsync` in `web-net/Data/FileOrganizerRepository.cs` set `is_manual = 0` but did not trigger `BulkUpdateTenantsAsync` for automatic reconciliation, unlike Python's `reset_document_lock` in `routes.py`.
3. **Timeline <-> Categories Navigation Parity**:
   - The 3-dots action item unconditionally said "Show in Timeline" (`.doc-menu-item-timeline`) and called `showDocInTimeline(doc)`. In Timeline view, it needed to be "Show in Categories" (`.doc-menu-item-categories`) and navigate to the document in Categories view.

## Key Changes
1. **Frontend Categories View (`src/api/static/js/categories-view.js`)**:
   - Added `getBatchTenantFromHash()` and `getBatchResolvedTenant()` to resolve open tenant from `currentTenant` or URL hash.
   - Updated `getBatchSelectedDocsInfo()` to prioritize open tenant (`openTenant = getBatchResolvedTenant()`).
   - Updated `renderTenantOptions()` so `matchedOption` (matching open tenant name/id) takes precedence over stale DOM `prevVal`.
   - Cleared `tenantSelect.value = ''` when opening move modal to prevent stale sticky values.
2. **Frontend Document Manager (`src/api/static/js/doc-manager.js`)**:
   - Added Pin / Unpin option in 3-dots menu (`.doc-menu-item-pin` / `.doc-menu-item-unpin`).
     - If `doc.is_manual == 1`, renders "Unpin Document" (`📌 إلغاء التثبيت • Unpin Document`), which calls `POST .../reset-lock` with fallback to `PATCH { is_manual: 0 }`, unlocking the document for auto-reconciliation.
     - If `doc.is_manual != 1`, renders "Pin Document" (`📌 تثبيت الوثيقة • Pin Document`), which calls `PATCH { is_manual: 1 }`, locking it permanently.
   - Detects current view: if in Timeline view (`currentTab === 'timeline'` or trigger button inside `#timeline-container`), renders "Show in Categories" (`📂 عرض في المجلدات • Show in Categories`).
   - Implemented `showDocInCategories(doc)`: switches to categories tab, opens folder (`openCategoryFolder`), scrolls to element, highlights with blue ring (`ring-4 ring-blue-500 bg-blue-50`), and selects document.
3. **Backend .NET (`web-net/Data/FileOrganizerRepository.cs`)**:
   - Updated `ResetDocumentLockAsync(string vaultId)` to trigger `BulkUpdateTenantsAsync(existing.HouseId, Array.Empty<TenantDto>(), reallocate: true)` immediately after resetting lock, matching Python backend behavior.
4. **Tri-Directory Asset Synchronization**:
   - Synchronized `categories-view.js` and `doc-manager.js` identically across `src/api/static/js/`, `web-net/wwwroot/js/`, and `dist/win-x64/wwwroot/js/` (0 diff verified).
5. **Automated Testing**:
   - Added 3 unit tests in `tests/frontend/components/batch_operations.test.js` validating open tenant preselection via `window.currentTenant`, URL hash `#tenant=...`, and `openBatchMoveForDoc`.
   - Added unit tests in `tests/frontend/components/doc_dropdown_and_date.test.js` for Pin/Unpin menu buttons, API calls, Timeline "Show in Categories" rendering, and `showDocInCategories` navigation.

## Verification
- **Frontend Vitest**: 25 test suites, 254 tests passing (`npm run test:frontend`).
- **Backend .NET xUnit**: 146 tests passing (`~/.dotnet/dotnet test`).
- **Backend Python pytest**: 31 tests passing (`test_document_management_api.py`, `test_v14_features.py`).
- **Static Assets**: 0 diff across all 3 static web trees.
