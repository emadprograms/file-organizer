# Quick Task Plan: Relocate Export Archive Button to Document Panel Header & Remove Bottom Archive Summary

## Objective
Remove the confusing and redundant digital archive summary section (`بيانات الأرشيف الرقمي للمنزل`) from the bottom of the House Profile, and relocate the Export House Archive button (`#btn-export-house-archive`) to the top Document Panel header right beside `#btn-manage-tenants` so it is permanently visible with 0 scrolling across all views (House Profile, Folders, and Timeline).

## Context & User Feedback
- User observed: When a house has multiple tenants, the digital archive summary box at the bottom (timespan, total scanned documents/pages, category counts breakdown) causes visual clutter and confusion. Furthermore, placing the archive download button at the bottom under tenant cards pushes the export button out of view, requiring extensive scrolling.
- Confirmed Solution:
  1. Strip the redundant `archiveBox` from the bottom of `renderHouseProfile(profile)` in `house-profile.js`.
  2. Relocate the export trigger button to the Document Panel header in `index.html` right next to the Folders/Timeline tab switcher and `#btn-manage-tenants`.
  3. Bind click handler to open `#export-archive-modal` with the active house profile, preserving full backward compatibility.

## Implementation Tasks
1. **Frontend HTML (`src/api/static/index.html`)**:
   - Inside `#document-list-panel` header, add `#btn-export-house-archive` button adjacent to `#btn-manage-tenants`.
2. **Frontend Component (`src/api/static/js/house-profile.js`)**:
   - In `renderHouseProfile(profile)`: Remove `archiveBox` creation and appending.
   - Implement `initExportArchiveHeaderButton()`: Wire click handler on `#btn-export-house-archive` (and `#btn-export-house-zip` for backward compatibility) to open `#export-archive-modal` using `currentHouseProfile` or fetch fallback.
   - Export `initExportArchiveHeaderButton` on `window`.
3. **Static Asset Synchronization**:
   - Rebuild ASP.NET Core web project via `~/.dotnet/dotnet build web-net/FileOrganizer.Web.csproj`.
   - Verify 0 diff via `diff -ru src/api/static/ web-net/wwwroot/`.
4. **Automated Testing**:
   - Update `tests/frontend/components/house_profile.test.js` to assert `بيانات الأرشيف الرقمي للمنزل` is not in `#document-list` and `#btn-export-house-archive` exists in header and opens modal.
   - Update `tests/frontend/components/export_archive_modal.test.js` to verify header button triggers modal.
   - Update `tests/frontend/test_house_register.py` assertions.
   - Run Vitest, Pytest, and xUnit suites.
5. **Documentation & Release**:
   - Update Milestone v14.0 documentation (`PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `v14.0-MILESTONE-AUDIT.md`, `MILESTONES.md`, and `milestones/v14.0-*`).
   - Git commit and push to `origin main`.
