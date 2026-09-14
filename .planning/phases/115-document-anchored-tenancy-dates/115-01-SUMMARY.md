# Phase 115 Plan 1: Document-Anchored Tenancy Dates & Minimalist Register Summary

**Phase**: 115
**Status**: Completed
**Date**: 2026-09-14
**Requirements Covered**: DAT-01, DAT-02, DAT-03, REG-01, REG-02, VER-01, VER-02, VER-03

## What Was Built / Changed

1. **Document-Anchored Start Date Derivation (`FileOrganizerRepository.cs` & `Program.cs`)**:
   - In `GetHouseProfileAsync` and `GetTenantsAsync`, the tenant's effective start date is automatically derived via a `LEFT JOIN` on `documents`:
     ```sql
     CASE 
         WHEN d.min_date IS NOT NULL AND d.min_date != '' 
              AND (t.start_date IS NULL OR t.start_date = '' OR t.start_date = '1970-01-01' OR t.start_date > d.min_date)
         THEN d.min_date 
         ELSE t.start_date 
     END AS StartDate
     ```
     where `d.min_date = MIN(primary_date)` for documents with `is_timeline_visible = 1`.
   - In `/api/ingest` in `Program.cs`, uploading a document automatically syncs the tenant's `StartDate` if it was previously empty/null or if the uploaded document has an earlier primary date.
   - For brand new tenants with zero documents, `StartDate` is nullable (`string?`), enabling creation without artificial date guessing.

2. **House Settings Modal UX (`tenant-manager.js`)**:
   - The `.tenant-start-input` field is no longer marked `required`, and displays placeholder `Auto (on first upload)` when empty.
   - Removed blocking validation `if (!start)` in `handleSaveTenants`, passing `start_date: start || null`.
   - Maintained user control over `end_date` and the `Present` checkbox.
   - Retained 12-column grid and two-way Resident $\leftrightarrow$ Applicant switching.

3. **Streamlined Minimalist House Profile Register (`house-profile.js`)**:
   - Cleaned up the tenancy register into a minimalist two-tier structure:
     - Residents section at top with simple title: `المستأجرون` (Tenants).
     - Exactly 1 clean divider line (`<hr class="border-t border-slate-200/80 dark:border-slate-700/80 my-3">`).
     - Applicants section at bottom with simple title: `المتقدمون` (Applicants).
     - Eliminated wordy boilerplate and confusing subtitle phrases.

4. **Automated Testing & Verification**:
   - Added `GetTenantsAsync_AnchorsStartDate_ToEarliestDocumentDate` and `AddTenantAsync_BrandNewTenantWithZeroDocuments_AllowsNullStartDate_AndSnapsOnFirstUpload` to `tests/HousingApplication.Tests/RepositoryTests.cs`.
   - Updated Vitest specifications in `applicant_workflow.test.js` and `house_profile.test.js`.
   - 161/161 backend .NET xUnit tests and 293/293 frontend Vitest tests passing cleanly (454 total).
