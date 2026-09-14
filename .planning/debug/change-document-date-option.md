---
status: resolved
trigger: "the user should be able to change the date if any document. that option isn't there. add that option in the 3 dots of any document."
created: 2026-09-14
updated: 2026-09-14
---

## Current Focus
- status: resolved
- resolution: "Added Change Date option to 3-dots dropdown menu, added Change Document Date modal, synced pages.resolved_date and primary_date in backend repository and frontend views"

## Symptoms
1. **Expected behavior**: In the 3-dots menu of any document (in categories view and timeline view), user can click "Change Date", choose a new date, and save. The document date updates immediately in the UI and database.
2. **Actual behavior**: The option "Change Date" was missing completely from the 3-dots menu.
3. **Error messages**: None (feature/option missing).
4. **Timeline**: Resolved in this session.
5. **Reproduction**: Clicking 3 dots on any document card previously only showed Rename, Move, Copy, Pin, Show in Timeline/Categories, Delete.

## Root Cause
1. `openDocDropdownMenu` in `src/HousingApplication.Web/wwwroot/js/doc-manager.js` only provided 6 action items and did not include a "Change Date" button.
2. No dedicated Change Document Date modal existed in the DOM or controller to allow entering a date and dispatching a `PATCH` request.
3. In `FileOrganizerRepository.UpdateDocumentAsync`, `primary_date` was updated on `documents`, but `pages.resolved_date` was not kept synchronized.

## Key Changes
1. **Backend (`FileOrganizerRepository.cs` & `DTOs.cs`)**:
   - Added `PrimaryDate` property to `DocumentActionResponseDto`.
   - Updated `UpdateDocumentAsync` to sync `pages.resolved_date = @PrimaryDate` when `primaryDate != null`.
   - Included `PrimaryDate` in `UpdateDocumentAsync` return object.
   - Updated unit test `UpdateDocumentAsync_UpdatesMetadataAndSyncsPages` in `RepositoryTests.cs`.
2. **UI Markup (`index.html`)**:
   - Added `change-doc-date-modal` with title, subtitle, date input, status container, and Cancel/Save buttons.
   - Added `doc-modal-date` input to `doc-action-modal` for full document management modal consistency.
3. **Frontend Controller (`doc-manager.js`)**:
   - Added `.doc-menu-item-date` ("Change Date" with calendar icon) to `openDocDropdownMenu`.
   - Implemented `openChangeDocDateModal(doc)`, `closeChangeDocDateModal()`, and `saveChangeDocDate()`.
   - On save: sends `PATCH /api/areas/{area}/houses/{house}/documents/{vaultId}` with `{ primary_date: newDate, is_manual: 1 }`.
   - Updates in-memory document references (`primary_date`, `date`, `dates`, `is_manual`), updates DOM badges (`.doc-date-badge` and timeline date text), and triggers view refresh.
   - Handled dynamic element creation in `ensureDateModalElements()` and detection of detached DOM nodes.
   - Exported functions to `window` and `module.exports`.
4. **Synchronization**:
   - Mirrored changes to `dist/win-x64/wwwroot/js/doc-manager.js` and `dist/win-x64/wwwroot/index.html`.
5. **Testing**:
   - Updated `tests/web/components/doc_dropdown_and_date.test.js` to assert 7 dropdown action buttons including `.doc-menu-item-date`.
   - Added comprehensive test suite for `openChangeDocDateModal` and `saveChangeDocDate`.
   - All 356 Vitest tests passing.
   - All 167 .NET xUnit tests passing.
