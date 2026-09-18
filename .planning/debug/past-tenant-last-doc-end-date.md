---
status: resolved
trigger: "if an end date of the previous tenant is not mentioned in the settings and he isn't marked as present then the date of his last document arrival is marked as the end date."
created: 2026-09-18
updated: 2026-09-18
---

## Root Cause
When a resident tenant was not marked as Present (i.e. past tenant) and no explicit end date was entered in House Settings, `end_date` remained null or empty. In earlier SQL queries and logic, `end_date IS NULL` was conflated with being actively present, leaving past tenants without an end date or incorrectly sorted as active.

## Resolution
1. **DTOs & Models**:
   - Added `IsPresent` (`bool?`) and `LastDocDate` (`string?`) to `TenantDto` and `Tenant`.
2. **Backend Repository (`FileOrganizerRepository.cs`)**:
   - `GetTenantsAsync`: Queries `d.max_date AS LastDocDate`. Identifies present vs previous residents. For previous residents with no explicit end date, assigns `effectiveEndDate = t.LastDocDate`.
   - `BulkUpdateTenantsAsync`: When persisting tenants, identifies non-present resident tenants without an explicit end date, queries `MAX(primary_date)` from `documents` for that tenant, and sets `end_date` to that arrival date.
   - `GetHousesAsync` & `GetTreeAsync` & `GetHouseProfileAsync`: Queries `d.max_date AS LastDocDate` and falls back to `t.LastDocDate` for non-active resident tenants with empty `end_date`.
3. **Frontend Modal (`tenant-manager.js`)**:
   - Pre-fills the End Date input with the last document arrival date for past tenants with no explicit end date.
   - Automatically populates the End Date input with the last document arrival date when "Present" is unchecked.
   - In `saveTenantsAndReallocate`, automatically includes the last document arrival date as `end_date` for non-present resident tenants without a user-specified end date.
   - Maintained 100% synchronization with `dist/win-x64/wwwroot/js/tenant-manager.js`.
4. **Automated Verification**:
   - Added unit tests in `tests/web/components/house_settings_modal.test.js`:
     - Verified pre-filling with last document arrival date on load.
     - Verified saving with last document arrival date when unmentioned by user.
     - 15/15 tests passed in `house_settings_modal.test.js` (626/626 vitest tests passed across all 43 files).
   - Added integration test `PastTenantWithoutExplicitEndDate_SetsEndDateToLastDocArrivalDate` in `tests/HousingApplication.Tests/RepositoryTests.cs`.
     - 979/979 .NET unit tests passed.
