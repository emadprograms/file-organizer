# Quick Task Summary: Relocate Export Archive Button to Document Panel Header & Remove Bottom Archive Summary

## Overview
Removed the confusing digital archive summary section from the bottom of the House Profile view and relocated the Export House Archive button to the top of the Document Panel header. The export trigger is now permanently visible across all views (Profile, Folders, and Timeline) with 0 scrolling.

---

## Context & Motivation
- **User Issue**:
  - The House Profile displayed a bottom section entitled `بيانات الأرشيف الرقمي للمنزل` with timespan (`من 2000 إلى 2026`), scanned archive count (`65 وثيقة (131 صفحة)`), and category breakdown badges (`11 - صور ومعاينات (11)`, `03 - أمر تخصيص (9)`, etc.).
  - When a house contained 5+ tenants, this section and the archive download button were pushed far below the fold, causing visual clutter and confusion.
  - The placement required excessive scrolling just to export house records.
- **User Preference**:
  - Pin the export button at the top of the Document Panel header next to the Folders/Timeline segmented tabs and House Settings (`#btn-manage-tenants`), ensuring it remains visible in every view without scrolling.
  - Cleanly display the Tenancy Register header and tenant cards in the House Profile without redundant category stats.

---

## Changes Implemented

### 1. Removed Bottom Archive Summary Box (`src/api/static/js/house-profile.js`)
- In `renderHouseProfile(profile)`:
  - Completely removed the `archiveBox` creation and rendering logic (timespan, total documents/pages, category counts tags, and bottom download button).
  - The House Profile now cleanly and focusedly renders the Tenancy Register header (`سجل المستأجرين المتعاقبين`) and tenant cards, directing users to click on tenant cards or view tabs.
  - Stored `currentHouseProfile = profile;` on render to ensure export state is consistently available.

### 2. Relocated Export Button to Document Panel Header (`src/api/static/index.html`)
- Inside `#document-list-panel` header, positioned right beside `#btn-manage-tenants`:
  ```html
  <button id="btn-export-house-archive" type="button" title="Export House Archive (ZIP / PDF Dossier) / تحميل أرشيف المنزل" class="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 border border-transparent hover:border-blue-200 rounded-lg transition-all flex items-center justify-center flex-shrink-0 cursor-pointer shadow-2xs" aria-label="Export House Archive">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
  </button>
  ```
- Styled consistently with modern toolbar action buttons (subtle slate border, hover transitions, Lucide-style download box icon).

### 3. Controller Binding & Backward Compatibility (`src/api/static/js/house-profile.js`)
- Implemented `initExportArchiveHeaderButton()`:
  - Selects `#btn-export-house-archive` and legacy `#btn-export-house-zip` (ensuring 100% backward compatibility with existing tests or scripts).
  - Handles active house detection (`currentHouseProfile`, `currentHouse`, `currentArea`), fallback profile fetching, and gracefully triggers `openExportArchiveModal(currentHouseProfile)`.
  - Initialized on DOM ready, modal initialization, and profile render.
  - Exported `initExportArchiveHeaderButton` on `window`.

### 4. ASP.NET Core Static Assets Synchronization
- Built `web-net/FileOrganizer.Web.csproj` using `~/.dotnet/dotnet build`.
- Verified 0 diff between `src/api/static/` and `web-net/wwwroot/` with `diff -ru src/api/static/ web-net/wwwroot/`.

---

## Verification & Test Results

1. **Frontend Vitest Component Suite (`npm run test:frontend`)**:
   - `tests/frontend/components/house_profile.test.js`:
     - Verified `بيانات الأرشيف الرقمي للمنزل` is no longer rendered in `#document-list`.
     - Verified `#btn-export-house-archive` exists in header and opens `#export-archive-modal`.
     - Verified backward compatibility for legacy `#btn-export-house-zip`.
   - `tests/frontend/components/export_archive_modal.test.js`:
     - Verified modal open trigger from header button and verified archive summary absence in `#document-list`.
   - **Result**: 109 tests passed across 10 test files (100% pass rate).

2. **Python Backend Pytest Suite**:
   - Command: `.venv/bin/pytest tests/test_v14_features.py tests/test_document_management_api.py -v`
   - **Result**: 28 passed in 3.73s (100% pass rate).

3. **ASP.NET Core xUnit Test Suite**:
   - Command: `~/.dotnet/dotnet test web-net/FileOrganizer.Tests/`
   - **Result**: 84 passed in 553ms (100% pass rate).
