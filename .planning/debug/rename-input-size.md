---
status: resolved
trigger: "when double clicking to rename, the name in which you can input the name is very small, make it bigger"
created: 2026-09-11
updated: 2026-09-11
---

## Symptoms
- **Expected**: Double-clicking document title opens a comfortably large, readable, and wide input box with clear font size and height for editing.
- **Actual**: The input element for renaming was very small (~22px height, 12px font) and width-constrained when original titles were short.
- **Errors**: None (UI/CSS sizing and container constraint issue).
- **Reproduction**: Double-click any document name in Categories view or Timeline view.

## Root Causes
1. **Container Width Constraints**:
   - In `categories-view.js`, the document title element (`titleSpan`) lacked `flex-1 min-w-0`. Inside the flex container, its width was shrink-wrapped to the original text length. For short titles (e.g. 2-4 characters in Arabic or English), the input element (having `w-full`) was compressed into a tiny horizontal box (~30px wide).
   - In `timeline-view.js`, the `h4.doc-title-text` similarly lacked `flex-1 min-w-0`.
2. **Clipping / Display Distortions on Title Elements**:
   - In `categories-view.js`, `titleSpan` had `truncate` (`overflow: hidden; text-overflow: ellipsis; white-space: nowrap`), which clipped the input and prevented natural expansion.
   - In `timeline-view.js`, `titleH4` had `line-clamp-2` (`display: -webkit-box; -webkit-box-orient: vertical`), which distorted the embedded `<input>` element.
3. **Small Input Dimensions and Typography**:
   - The `<input>` had `text-xs font-normal px-1.5 py-0.5`, giving only 12px font size and ~22px total height, which was cramped and hard to read, especially for Arabic script.
   - It lacked `dir="auto"`, leading to improper text alignment for mixed Arabic and English document titles.

## Resolution
1. **Expanded Title Containers**:
   - Added `flex-1 min-w-0` to `titleSpan` in `src/api/static/js/categories-view.js` and `titleH4` in `src/api/static/js/timeline-view.js`. This allows the title container and its inline rename input to expand across the full available row width.
2. **Temporarily Removed Display Clamps During Editing**:
   - In `categories-view.js`, removed `truncate` class on double-click and restored it upon commit or cancellation.
   - In `timeline-view.js`, removed `line-clamp-2` class on double-click and restored it upon commit or cancellation.
3. **Enlarged Input Field and Added BiDi Support**:
   - Upgraded input styling in both views to:
     `type="text" dir="auto" class="inline-rename-input px-3 py-1.5 text-sm font-medium border-2 border-blue-500 rounded-lg bg-white text-slate-900 shadow-sm focus:outline-hidden focus:ring-2 focus:ring-blue-500/30 w-full min-w-0"`
   - Increased font size to `text-sm` (14px) and padding to `px-3 py-1.5` (yielding ~34px height).
   - Added `dir="auto"` for proper Arabic/English text alignment.
   - Added `shadow-sm` and `border-2 border-blue-500` for clear visual focus.
4. **Asset Synchronization**:
   - Synchronized changes to `web-net/wwwroot/js/categories-view.js` and `web-net/wwwroot/js/timeline-view.js` via `dotnet build`.
5. **Testing**:
   - Added comprehensive tests in `tests/frontend/components/inline_rename.test.js` validating:
     - `text-sm`, `px-3`, `py-1.5`, `dir="auto"` on inline rename input.
     - `flex-1 min-w-0` on container elements.
     - Toggling of `truncate` in Categories view and `line-clamp-2` in Timeline view during and after renaming.

## Verification
- `npm run test:frontend`: All 109 tests passed across 10 test files.
- `~/.dotnet/dotnet test web-net/FileOrganizer.Tests/`: All 84 tests passed.
- `.venv/bin/pytest tests/test_document_management_api.py`: All 13 tests passed.
