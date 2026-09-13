# Phase 114 Plan 1: Settings Modal Simplification & Applicant Clean-Up Summary

**Phase**: 114
**Status**: Completed
**Date**: 2026-09-13
**Requirements Covered**: SET-01, SET-02, SET-03, VAC-01, VER-01, VER-02

## What Was Built / Changed
1. **Tenant Modal UI Streamlining (`index.html`)**:
   - Removed the `Notes` column header from the `#tenant-modal` table.
   - Rebalanced grid columns across a clean 12-column layout:
     - Name: 4 columns (`sm:col-span-4`)
     - Type: 2 columns (`sm:col-span-2`)
     - Start Date: 2 columns (`sm:col-span-2`)
     - End Date: 2 columns (`sm:col-span-2`)
     - Present: 1 column (`sm:col-span-1`)
     - Delete: 1 column (`sm:col-span-1`)

2. **Tenant Manager Script Simplification (`tenant-manager.js`)**:
   - Removed the `.tenant-notes-input` field and wrapper from dynamically created tenant rows in `addTenantRow`.
   - Aligned row input grid spans with the 12-column modal header.
   - Simplified `handleSaveTenants` to omit client-side notes (payload sends `notes: null`), preserving database compatibility while eliminating clutter.

3. **Applicant Card Clean-Up (`house-profile.js`)**:
   - Removed `notesHtml` snippet and the `.applicant-notes` badge from applicant card rendering in `renderHouseProfile`.
   - Retained clean presentation of name, applicant badge (`📋 متقدم (لم يسكن)`), application date, and document/category counts.

4. **Vacated Tenancy Safeguard (`Program.cs`)**:
   - Updated `/api/ingest` date conflict check to explicitly require `resolvedTenant.IsResident == 1` alongside non-empty `EndDate`.
   - Prevented non-resident applicants (`IsResident == 0`) from triggering spurious vacated tenant warnings (`tenancy_date_conflict`) when documents dated after application/order dates are ingested.

5. **Test Updates & Verification**:
   - Updated Vitest specifications in `tests/web/components/house_settings_modal.test.js`, `tests/web/components/applicant_workflow.test.js`, and `tests/web/components/house_profile.test.js` to assert absence of `.tenant-notes-input` and `.applicant-notes`.
   - Added `PostIngest_ApplicantNonResident_WithFutureDate_DoesNotConflict_AndSucceeds` to `tests/HousingApplication.Tests/ApiEndpointTests.cs` to guarantee backend safety.
   - Verified 159/159 .NET tests passing and 293/293 web tests passing.
