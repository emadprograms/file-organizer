---
status: complete
task_id: 260911-nh7
slug: viewer-category-badge-header
date: 2026-09-11
---

# Quick Task Summary: Replace Tenant Selector with Category Badge in Document Viewer Header

**Task ID**: `260911-nh7` (QCK-23)  
**Status**: Complete  
**Date**: 2026-09-11  

---

## 1. Overview
Replaced the confusing and misplaced tenant dropdown in the Document Viewer and Live Peek header (`#viewer-tenant-select`) with a clean, intuitive Category badge (`#viewer-category-badge`):
- When opening a document or hovering in Live Peek mode, users now see the document's category (e.g., `05 - عقود`, `06 - كهرباء وماء`, `13 - رسائل متنوعة`) clearly identified in the header bar with a dedicated folder icon and badge styling.
- Removed `#viewer-tenant-select` and `#viewer-tenant-label` from the viewer panel header. (Tenant manual assignment is already cleanly handled in the Document Action Modal).
- Enforced instant category resolution across all views (`categories-view`, `timeline-view`, `pdf-preview`, `command-palette`), resolving from passed arguments, `currentTimeline`, `getSelectedDoc()`, `globalTreeData`, or async metadata API fallback.

## 2. Changes Made
1. **`src/api/static/index.html`**:
   - Replaced `#viewer-tenant-label` and `#viewer-tenant-select` with `#viewer-category-badge` and `#viewer-category-val`.
   - Bumped cache bust versions for affected scripts to `?v=260911-34`.
2. **`src/api/static/js/doc-viewer.js`**:
   - Added `updateViewerCategory(vaultId, explicitCategory)` supporting multi-source resolution (argument, timeline, active doc, tree data, metadata API).
   - Updated `openDocument` and `peekDocument` to call `updateViewerCategory(vaultId, category)` and display the category badge in both full view and Live Peek.
   - Updated `closeDocument()` to reset the category badge.
   - Removed calls to `updateViewerTenantSelect`. Exposed `window.updateViewerCategory`.
3. **`src/api/static/js/tenant-manager.js`**:
   - Deprecated `updateViewerTenantSelect` into a safe no-op stub to prevent unwanted network fetches or DOM searches.
4. **`src/api/static/js/categories-view.js`**:
   - Ensured `doc.category = doc.category || cat.name` is always initialized on documents.
   - Passed `doc.category || cat.name` to `openDocument`.
5. **`src/api/static/js/timeline-view.js`**:
   - Passed `doc.category` to `openDocument`.
6. **`src/api/static/js/pdf-preview.js`**:
   - Passed `docCategory` to `peekDocument` in `attachPreview` and `showPreview`.
   - Passed `docCategory` to `openDocument` in `quickLookOpenFull`.
7. **`src/api/static/js/command-palette.js`**:
   - Passed `d.category || d.folder` to `openDocument`.
8. **Tri-Directory Asset Parity**:
   - Synchronized all changes to `web-net/wwwroot/` and `dist/win-x64/wwwroot/` with 0 diff.
9. **Automated Test Coverage**:
   - Created `tests/frontend/components/doc_viewer.test.js` (6 unit tests).
   - Updated `tests/frontend/components/inline_rename.test.js` assertion for `openDocument`.
   - Updated `tests/frontend/test_v11_e2e_db.py` (`test_viewer_category_badge_e2e`) verifying the category badge is visible and tenant selector is removed.

## 3. Verification
- Vitest Frontend Suite: 176 / 176 passed across 19 files.
- Playwright E2E Suite (`test_v11_e2e_db.py`): 13 / 13 passed in 17.14s.
- Python Backend API Tests: 14 / 14 passed in `test_tenant_reallocation_api.py` and `test_tenant_repository_unit.py`.
- ASP.NET Core xUnit Suite: 85 / 85 passed.
- Static Asset Parity: `diff -ru` = 0 across all three directories.
