---
status: resolved
trigger: "when I click on show in categories. it doesn't open the folder or point to the file. It just opens the categories tab and that is all."
created: 2026-09-17
updated: 2026-09-17
---

## Current Focus
- hypothesis: "RESOLVED: showDocInCategories previously failed to open the folder and point to the file due to: (1) missing tenant route update when called from house timeline, which caused refreshCurrentTab to load the house profile registry rather than categories; (2) strict equality matching in openCategoryFolder and renderCategories between raw category strings and prefixed folder card names; and (3) clearing of openCategoryNames during asynchronous category loads."
- test: "Full test suite execution (Vitest 518 tests, .NET 956 tests) including dedicated unit and integration tests in tests/web/components/doc_dropdown_and_date.test.js."
- expecting: "All tests pass with 100% dual-asset parity between src/ and dist/."
- next_action: "Commit and push changes."

## Symptoms
1. **Expected behavior**: When clicking 'Show in Categories' on any document from the timeline, the application switches to the Categories tab for that document's tenant, opens/expands the folder containing that document, scrolls the document row into view, and highlights it.
2. **Actual behavior**: It only switches to the categories tab, but does not open the folder or scroll/point to the file.
3. **Error messages**: None.
4. **Timeline**: Resolved in this session.
5. **Reproduction**: In the timeline view (either house or tenant timeline), click the 3-dots action menu on any document and click 'Show in Categories'.

## Root Causes Identified
1. **Missing Tenant Route Navigation**:
   In `doc-manager.js`, `showDocInCategories` set local `currentTenant` and `window.currentTenant`, then invoked `tabCategories.click()`. However, `router.js` checks `if (!currentTenant)` where `currentTenant` was its internal module closure variable (null when in House Timeline mode). This triggered `loadHouseProfile` (the tenants registry `سجل المستأجرين`) instead of `loadCategories`, leaving the category folders unrendered.
2. **Category Name Format Mismatch**:
   In timeline documents, `doc.category` is often stored without the numeric folder prefix (e.g. `"عقود"` or `"استقطاع إيجار"`), whereas category cards rendered in `categories-view.js` use numbered prefixes (e.g. `"05 - عقود"`). `openCategoryFolder` and `findAndHighlight` checked only strict string equality (`c.getAttribute('data-category-name') === categoryName`), failing to locate and open the folder card.
3. **Folder State Erasure on Asynchronous Load**:
   `loadCategories` loads asynchronously. When it calls `renderCategories()`, `openCategoryNames.clear()` was executed on initial load or scope changes, discarding any folder pre-opened before the DOM rendering finished.

## Resolution
1. **Category Matching Helper (`categories-view.js`)**:
   - Implemented `normalizeCategoryName(name)` and `isCategoryMatch(nameA, nameB)` to compare category names across standard and custom prefix variations (`"05 - عقود"` vs `"عقود"`).
   - Updated `openCategoryFolder(categoryName)` to match cards using `isCategoryMatch` and unhide their `.category-docs`.
   - Updated `renderCategories()` to preserve `window._pendingOpenCategory` on scope changes and initial loads.
   - Updated folder card rendering to expand matching folders if registered in `openCategoryNames` or matching `window._pendingOpenCategory`.
2. **Tenant Route Navigation & Robust Polling (`doc-manager.js`)**:
   - Updated `showDocInCategories(doc)` to register `window._pendingOpenCategory = docCategory`.
   - Navigates to the tenant route hash (`#/area/.../house/.../tenant/...`) when `docTenant` is present.
   - Enhanced `findAndHighlight` polling to identify parent folders using `isCategoryMatch`, unhide parent folder documents, scroll the target row into view with centering, apply a visual pulse ring animation, and select the document in viewer.
3. **Router State Synchronization (`router.js`)**:
   - Updated `refreshCurrentTab` to synchronize `currentTenant` with `window.currentTenant` if present.
4. **Dual-Asset Parity**:
   - Synchronized all changes to `dist/win-x64/wwwroot/js/categories-view.js`, `dist/win-x64/wwwroot/js/doc-manager.js`, and `dist/win-x64/wwwroot/js/router.js` with 0 diff lines.
5. **Testing**:
   - Added unit tests in `tests/web/components/doc_dropdown_and_date.test.js` verifying `isCategoryMatch`, unprefixed category matching against prefixed DOM cards, `renderCategories` preservation of pending categories, and navigation.
   - All 518 Vitest tests passed. All 956 .NET tests passed.
