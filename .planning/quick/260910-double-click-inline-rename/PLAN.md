# Quick Task Plan: Double-Click Inline Document Renaming in Categories and Timeline Views

**Task ID**: `260910-double-click-inline-rename`  
**Milestone**: v14.0 Power-User Operations & Portfolio Expansion (QCK-05)  
**Status**: Completed  

---

## 1. Context & User Request

The user requested:
> "double clicking the filename should allow you to rename it. in both categories and timeline. spawn a subagent to do this and update the docs."

Backend APIs across both Python FastAPI (`src/api/routes.py`) and ASP.NET Core 8.0 Minimal APIs (`web-net/Program.cs`) already support document title updates via `PATCH /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}` with `{ "arabic_title": "new title" }`.

Prior to this feature, renaming a document required opening the 3-dots action menu (`...`) and submitting the full Document Action Modal. Enabling direct double-click inline renaming streamlines workflows for power users reviewing documents in both category folder drill-downs and chronological timelines.

---

## 2. Technical Objectives

1. **Categories View Component (`src/api/static/js/categories-view.js`)**:
   - Update document title span in `renderCategories` with class `doc-title-text cursor-text flex-1 min-w-0` and tooltip `title="Double-click to rename"`.
   - Attach `ondblclick` event handler:
     - Stop event propagation and prevent default browser text selection.
     - Dynamically un-clamp by removing `truncate` during active editing.
     - Swap title contents with a prominent, comfortable inline `<input type="text" dir="auto" class="inline-rename-input px-3 py-1.5 text-sm font-medium border-2 border-blue-500 rounded-lg bg-white text-slate-900 shadow-sm focus:outline-hidden focus:ring-2 focus:ring-blue-500/30 w-full min-w-0">` pre-filled with the current title.
     - Isolate `click`, `dblclick`, `mousedown`, and `dragstart` on the input to prevent card selection or card dragging.
     - Automatically focus and select all text in the input.
     - On `Enter` or `blur`: commit title change if non-empty and changed.
     - On `Escape`: cancel edit, restore `truncate`, and restore original title without sending network requests.
     - On commit: call `PATCH /api/areas/{area}/houses/{house}/documents/{vault_id}` with `{ "arabic_title": newTitle }`, update in-memory doc (`brief_arabic_title` and `filename`), restore `truncate`, update DOM text and tooltip, and display success toast feedback.
     - On error: display error toast, restore `truncate`, and revert to original title.
     - If empty or unchanged: revert to original title without sending network requests.

2. **Timeline View Component (`src/api/static/js/timeline-view.js`)**:
   - Update document card title `<h4>` in `renderTimeline` with class `doc-title-text cursor-text flex-1 min-w-0` and tooltip `title="Double-click to rename"`.
   - Attach `ondblclick` event handler with identical inline editing, dynamic removal of `line-clamp-2` during edit, keyboard shortcuts (`Enter`/`Escape`/`blur`), event isolation (preventing `card.onclick` from opening the document during rename), and PATCH backend integration.

3. **Dual-Backend Parity & ASP.NET Core Static Asset Sync (`web-net/wwwroot/`)**:
   - Execute `~/.dotnet/dotnet build web-net/FileOrganizer.Web.csproj` to copy updated static JS assets to `web-net/wwwroot/`.
   - Verify zero diff between `src/api/static/` and `web-net/wwwroot/`.

4. **Automated Testing**:
   - Create Vitest unit test suite `tests/frontend/components/inline_rename.test.js` covering:
     - Categories view double-click input transformation.
     - Timeline view double-click input transformation and event isolation.
     - Enter key commit, PATCH API call, in-memory doc update, DOM update, toast feedback.
     - Escape key cancellation and original title restoration without fetch.
     - Blur committing when changed and restoring when unchanged.
     - Empty/whitespace input rejection without fetch.
     - Graceful HTTP error handling with error toast and restoration.
   - Verify all test suites pass (108 Vitest, 84 xUnit, 28 pytest).

5. **Milestone Documentation**:
   - Update all Milestone v14.0 documentation files: `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `v14.0-MILESTONE-AUDIT.md`, `MILESTONES.md`, and `milestones/v14.0-*`.
