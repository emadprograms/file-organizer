# Quick Task 260912-vacated-tenant-date-conflict: Vacated Tenant Document Date Conflict & Tenancy Extension Prompt

## Problem
When a user attempts to add or ingest a document for a tenant who has vacated the property in prior years (e.g., vacated in 2024), but the document date is modern or today's date (e.g. 2026-09-12), the system previously allowed or forced ingestion without warning. This caused date inconsistencies where past tenants accumulated documents dated years after their vacation without confirmation or opportunity to extend their tenancy dates.

## User Request
"another thing is that if a user tries to add document for any tenant with today's date but he vacated the house in 2024. the program should throw an error saying that this person has vacated at so and so and you are trying to add the document dated so so. do you want to extend his date or what? make tests. update milestone docs. commit and push."

## Solution
1. **Backend Conflict Detection & Extension API Parity**:
   - Python FastAPI (`src/api/routes.py`):
     - Added `is_doc_date_after_vacated(primary_date, tenant.end_date)` date comparison.
     - Added `extend_tenant_date`, `confirm_date_mismatch`, and `new_end_date` Form fields to `/api/ingest`.
     - When a conflict occurs without confirmation flags, throws HTTP 400 Bad Request with detail: `"Tenant '{name}' vacated on {end_date} and you are trying to add a document dated {doc_date}. Do you want to extend his date?"`.
     - When `extend_tenant_date=True`, updates the tenant's `end_date` in the database to `primary_date` (or `new_end_date`) and proceeds with document creation.
     - When `confirm_date_mismatch=True`, allows adding the document under the vacated tenant without altering tenant records.
   - ASP.NET Core 8.0 (`web-net/Program.cs`, `web-net/Common/TextUtils.cs`, `web-net/Data/FileOrganizerRepository.cs`):
     - Added `TextUtils.IsDocDateAfterVacated(primaryDate, resolvedTenant.EndDate)`.
     - Added `IFileOrganizerRepository.UpdateTenantDatesAsync(tenantId, startDate, endDate)` in repository.
     - In `/api/ingest`, throws 400 with structured JSON and error message on unconfirmed conflict, updates tenant dates when `extend_tenant_date=true`, and permits bypass when `confirm_date_mismatch=true`.

2. **Frontend Ingest UI & Conflict Modal**:
   - Added `#vacated-tenant-modal` in `index.html` across all 3 web root templates with light & dark mode styling.
   - In `ingest-station.js`:
     - Stored `endDate` and `startDate` on tenant select options, displaying `(${start_year} - ${end_year}) [Vacated]` in dropdown option labels.
     - Implemented `isDocDateAfterVacated` and `promptVacatedTenantConflict(tenantName, endDate, docDate)`.
     - In `submitSingleIngest`, intercepts date conflict and displays modal with three user actions:
       1. "تمديد تاريخ المستأجر ورفع الوثيقة / Extend Tenancy Date & Upload" (sends `extend_tenant_date=true`).
       2. "رفع دون تمديد / Upload Without Extending" (sends `confirm_date_mismatch=true`).
       3. "إلغاء / Cancel" (closes modal and focuses date input).
     - In `submitHouseBatchIngest`, checks batch queue items against selected tenant and prompts user before uploading.
   - Synchronized static assets across `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/` with zero diff.

3. **Multi-Stack Verification**:
   - .NET xUnit test in `ApiEndpointTests.cs`: `PostIngest_VacatedTenant_WithFutureDate_ReturnsBadRequest_OrExtendsDate`.
   - Python Pytest in `test_api_v11.py`: `test_ingest_vacated_tenant_date_conflict`.
   - Vitest frontend tests in `ingest_station.test.js`: `isDocDateAfterVacated`, `promptVacatedTenantConflict`, and `submitSingleIngest`.
