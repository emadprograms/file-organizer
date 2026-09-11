---
status: resolved
trigger: "when I click on the 3 dots of the document to copy or move and then click on copy. it automatically activates the multi-select feature and enables the check and shows the multiselect option as well. fix this bug."
created: 2026-09-12
updated: 2026-09-12
---

## Symptoms
- **Expected**: Clicking the 3-dots action menu on an individual document and selecting "Copy Document" or "Move Document" should open the copy or move modal solely targeting that document, without activating batch multi-select mode, without checking the document's checkbox, and without showing the bottom floating multi-select action bar (`#batch-action-bar`).
- **Actual**: Clicking "Copy" or "Move" in the 3-dots dropdown menu cleared and populated `selectedDocIds` with that document ID, checked the card's checkbox (`.doc-select-checkbox`), and invoked `updateBatchActionBar()` which revealed the floating batch action bar.
- **Reproduction**:
  1. Open a house in categories view.
  2. Click the 3-dots menu on any document card.
  3. Click "Copy Document" (or "Move Document").
  4. The copy/move modal appeared, but simultaneously the document's checkbox turned checked and the bottom batch action bar popped up.

## Root Causes
In `categories-view.js`, `openBatchMoveForDoc(doc)` and `openBatchCopyForDoc(doc)` were originally implemented as lazy shortcuts that routed single document actions through the multi-select batch mechanism:
```javascript
selectedDocIds.clear();
selectedDocIds.add(doc.vault_id);
updateBatchActionBar();
document.querySelectorAll('.doc-select-checkbox').forEach(cb => {
    cb.checked = (cb.dataset.vaultId === doc.vault_id);
});
openBatchMoveModal(); // or openBatchCopyModal()
```
Because they populated `selectedDocIds` and called `updateBatchActionBar()`, the UI entered multi-select batch mode for a single-item operation.

## Resolution
1. **Dedicated Single Target State**:
   - Introduced `let singleTargetDoc = null;` in `categories-view.js` to decouple single-document operations from the global `selectedDocIds` Set.
   - Refactored `openBatchMoveForDoc(doc)` and `openBatchCopyForDoc(doc)` to simply assign `singleTargetDoc = doc;` and directly launch the respective modal without modifying `selectedDocIds`, without touching checkbox states in the DOM, and without calling `updateBatchActionBar()`.
2. **Modal and Payload Adaptation**:
   - Updated `openBatchMoveModal` and `openBatchCopyModal` to allow opening when either `selectedDocIds.size > 0` or `singleTargetDoc` is set.
   - Customized modal subtitles to display the document name (`Move "{name}" to a target category folder.`) when operating on a single document.
   - Updated `handleBatchMoveSubmit` and `handleBatchCopySubmit` to send `vault_ids: [singleTargetDoc.vault_id]` when `singleTargetDoc` is active, clear `singleTargetDoc = null;`, and bypass clearing multi-select checkboxes.
   - Updated `closeBatchMoveModal` and `closeBatchCopyModal` to reset `singleTargetDoc = null;`.
   - Adapted `getBatchSelectedDocsInfo()` to read tenant information from `singleTargetDoc` when active.
3. **Multi-Stack Parity & Full Test Suite**:
   - Synchronized static assets across `web-net/wwwroot/`, `src/api/static/`, and `dist/win-x64/wwwroot/` with 0 diff.
   - Updated `tests/frontend/components/doc_dropdown_and_date.test.js` with comprehensive unit tests verifying that multi-select is NOT activated, checkboxes remain unchecked, action bar remains hidden, and single move/copy endpoints are called properly.
   - All 22 Vitest frontend test suites passed (193 tests).
   - All 120 .NET xUnit tests passed.
   - All 18 Python pytest tests passed.
