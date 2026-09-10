---
status: resolved
trigger: Clicking on 'Delete Document' isn't closing the dialog.
---
# Debug Session: Delete Document Modal Not Closing

## Symptoms
- In the Document Management dialog (`doc-manager.js`), clicking "Delete Document" and confirming deletion did not close the modal dialog.
- The document might fail to delete with a 404 error if area/house identifiers were unresolved.
- If an error occurred in post-deletion UI refreshes (such as `window.refreshCurrentTab` or `showToast`), the modal remained open in an unclosed state.
- Even when CSS classes (`hidden`) were toggled, missing inline style overrides (`style.display = 'none'`) could lead to display conflicts.

## Root Causes
1. **Unresolved Area and House Context**:
   - `handleDeleteDoc` attempted to resolve `area` and `house` with:
     ```javascript
     const area = (typeof currentArea !== 'undefined' && currentArea) ? currentArea : (activeDocModalDoc.area_id || '');
     const house = (typeof currentHouse !== 'undefined' && currentHouse) ? currentHouse : (activeDocModalDoc.house_id || '');
     ```
   - Documents passed from `categories-view.js` and `timeline-view.js` do not carry `.area_id` or `.house_id` properties.
   - When `currentArea` was lexical null or only set on `window.currentArea` / URL hash (`#/area/.../house/...`), `area` and `house` resolved to empty strings `""`.
   - The DELETE request was dispatched to `/api/areas//houses//documents/{vault_id}`, returning 404 and throwing an error before `closeDocModal()` could be reached.
2. **Sequencing of Dialog Dismissal**:
   - `closeDocModal()` was previously positioned after `showToast` and before `refreshCurrentTab`. If any toast notification or UI refresh logic failed or rejected, the modal was never closed.
3. **Display Specificity**:
   - `closeDocModal()` only manipulated CSS class lists (`classList.add('hidden')`, `classList.remove('flex')`) without explicitly clearing inline `style.display = 'none'`, leaving room for CSS specificity conflicts if inline styles were altered.
4. **Missing Inline Handlers**:
   - The HTML buttons (`#btn-doc-delete`, `#doc-modal-close`, `#doc-modal-cancel`) in `index.html` lacked inline `onclick` fallbacks to `window.handleDeleteDoc` and `window.closeDocModal`.

## Resolution

### 1. Robust Area/House Resolution in `src/api/static/js/doc-manager.js`
- Added `getAreaFromHash()` to extract area IDs from URL hash matching `#/area/([^/]+)` (stripping any `area_` prefix).
- Added `getHouseFromHash()` to extract house IDs from URL hash matching `house/([^/]+)`.
- Added hierarchical resolvers `getResolvedArea(explicitDoc)` and `getResolvedHouse(explicitDoc)` checking:
  1. `explicitDoc.area_id` / `explicitDoc.house_id`
  2. `activeDocModalDoc.area_id` / `activeDocModalDoc.house_id`
  3. Lexical scope `currentArea` / `currentHouse`
  4. Global scope `window.currentArea` / `window.currentHouse`
  5. URL hash fallback via `getAreaFromHash()` / `getHouseFromHash()`
- Updated `openDocModal(doc, currentCategory)` to attach resolved `area_id` and `house_id` to `activeDocModalDoc` and set `docActionModal.style.display = 'flex'`.
- Updated `closeDocModal()` to explicitly set `docActionModal.style.display = 'none'`.
- Updated `saveDocModal`, `resetDocLock`, `populateTenantOptions`, and drag-and-drop handlers to use `getResolvedArea()` and `getResolvedHouse()`.
- Exposed `getResolvedArea` and `getResolvedHouse` to `window` and `module.exports`.

### 2. Immediate Modal Dismissal in `handleDeleteDoc`
- In `handleDeleteDoc(e)`:
  - Added event checks: `if (e) { e.preventDefault?.(); e.stopPropagation?.(); }`.
  - Guarded against missing active document.
  - User confirmation prompt retained.
  - Extracted area/house via resolution helpers.
  - Dispatched DELETE request via `fetch`.
  - Immediately invoked `closeDocModal()` upon `res.ok` before any background UI refreshes.
  - Wrapped subsequent UI refreshes (`showToast`, `window.refreshCurrentTab`, `window.loadTree`) in a dedicated try/catch block so post-delete UI refresh rejections do not interrupt or reopen the modal.

### 3. Inline Event Handlers in `src/api/static/index.html`
- Added inline `onclick="if(typeof window.handleDeleteDoc==='function')window.handleDeleteDoc(event);"` to `#btn-doc-delete`.
- Added inline `onclick="if(typeof window.closeDocModal==='function')window.closeDocModal();"` to `#doc-modal-close` and `#doc-modal-cancel`.

### 4. Build & Sync to `web-net/wwwroot`
- Compiled `web-net/FileOrganizer.Web.csproj` with dotnet build, automatically synchronizing static assets to `web-net/wwwroot/`. Verified with `diff` that `web-net/wwwroot/js/doc-manager.js` and `web-net/wwwroot/index.html` are identical to `src/api/static/`.

## Verification & Automated Tests
1. **Frontend Vitest (`npm run test:frontend`)**:
   - Verified existing deletion cancellation and deletion tests.
   - Added test: `sets style.display = "none" and adds hidden class on closeDocModal`.
   - Added test: `resolves area and house from window.currentArea and window.currentHouse when not on global and closes modal`.
   - Added test: `falls back to URL hash resolution when global and window properties are absent`.
   - Added test: `ensures modal remains closed even if refreshCurrentTab rejects with an error`.
   - Result: 67 passed (4 test files).
2. **Playwright End-to-End (`.venv/bin/pytest tests/frontend/test_delete_doc_dialog_playwright.py`)**:
   - Tested real DOM interaction: open modal via 3-dot menu on category card, confirm deletion, verify dialog closes and is hidden.
   - Result: 1 passed (100%).
3. **Backend Python API (`.venv/bin/pytest tests/test_document_management_api.py`)**:
   - Result: 13 passed (100%).
4. **.NET Tests (`~/.dotnet/dotnet test web-net/FileOrganizer.Tests/`)**:
   - Result: 43 passed (100%).
