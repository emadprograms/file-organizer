---
status: complete
date: 2026-09-12
task_id: 260912-vacated-tenant-date-conflict
---

# Quick Task 260912-vacated-tenant-date-conflict: Vacated Tenant Document Date Conflict & Tenancy Extension Prompt

## Overview
When a user attempts to add or ingest a document for a tenant who has already vacated a property in prior years (e.g. vacated in 2024), but the document date is modern or today's date (e.g. 2026-09-12), the system now detects the date mismatch, informs the user with an explicit prompt, and offers options to either extend the tenant's residency period or upload the document without altering the tenant's dates.

## User Request
"another thing is that if a user tries to add document for any tenant with today's date but he vacated the house in 2024. the program should throw an error saying that this person has vacated at so and so and you are trying to add the document dated so so. do you want to extend his date or what? make tests. update milestone docs. commit and push."

## Changes Made

### 1. ASP.NET Core 8.0 Minimal API Backend
- **`web-net/Common/TextUtils.cs`**:
  - Implemented `IsDocDateAfterVacated(string? docDateStr, string? tenantEndDateStr)` helper handling both 4-digit years (`YYYY`) and standard ISO dates (`YYYY-MM-DD`).
- **`web-net/Data/IFileOrganizerRepository.cs` & `web-net/Data/FileOrganizerRepository.cs`**:
  - Added `Task<bool> UpdateTenantDatesAsync(int tenantId, string? startDate, string? endDate)` to update tenant dates in SQLite.
- **`web-net/Program.cs`**:
  - In `/api/ingest`, added conflict check comparing `primary_date` against `resolvedTenant.EndDate`.
  - When `primary_date > tenant.EndDate` and neither `extend_tenant_date` nor `confirm_date_mismatch` is set, returns HTTP 400 Bad Request with structured JSON:
    `{ "error": "Tenant '{resolvedTenant.Name}' vacated on {resolvedTenant.EndDate} and you are trying to add a document dated {primaryDate}. Do you want to extend his date?", "code": "VACATED_TENANT_DATE_CONFLICT", ... }`.
  - When `extend_tenant_date` is `true`, calls `repo.UpdateTenantDatesAsync(resolvedTenant.Id, resolvedTenant.StartDate, newEndDate)` to update the database record before proceeding with ingestion.
  - When `confirm_date_mismatch` is `true`, proceeds with document ingestion under the vacated tenant without altering tenant dates.
- **`web-net/FileOrganizer.Tests/ApiEndpointTests.cs`**:
  - Added unit test `PostIngest_VacatedTenant_WithFutureDate_ReturnsBadRequest_OrExtendsDate`.
  - All 148 xUnit tests pass.

### 2. Python FastAPI Backend
- **`src/api/routes.py`**:
  - Implemented `is_doc_date_after_vacated(doc_date_str, tenant_end_date_str)` with ISO & year-level comparison.
  - In `ingest_document`, added Form fields `extend_tenant_date: bool`, `confirm_date_mismatch: bool`, and `new_end_date: Optional[str]`.
  - Validates `primary_date` against `target_t.end_date`. If conflict occurs and no confirmation flags are present, raises HTTP 400 with detail:
    `"Tenant '{target_t.name}' vacated on {target_t.end_date} and you are trying to add a document dated {primary_date}. Do you want to extend his date?"`.
  - When `extend_tenant_date` is true, updates the tenant's `end_date` in SQLite and proceeds.
  - When `confirm_date_mismatch` is true, records document under the vacated tenant without altering tenant dates.
- **`tests/test_api_v11.py`**:
  - Added unit test `test_ingest_vacated_tenant_date_conflict`.
  - All 44 pytest tests pass.

### 3. Web Frontend & UI Components
- **`src/api/static/index.html`**, **`web-net/wwwroot/index.html`**, **`dist/win-x64/wwwroot/index.html`**:
  - Added `#vacated-tenant-modal` interactive conflict dialog styled for both light and dark themes.
  - Displays explicit warning in Arabic and English, showing the tenant's vacation date and the document's date.
  - Features three distinct action buttons:
    1. `تمديد تاريخ المستأجر ورفع الوثيقة / Extend Tenancy Date & Upload` (`#btn-vacated-modal-extend`)
    2. `رفع دون تمديد / Upload Without Extending` (`#btn-vacated-modal-upload-as-is`)
    3. `إلغاء / Cancel` (`#btn-vacated-modal-cancel`)
- **`src/api/static/js/ingest-station.js`**, **`web-net/wwwroot/js/ingest-station.js`**, **`dist/win-x64/wwwroot/js/ingest-station.js`**:
  - Populated `dataset.endDate` on tenant selection `<option>` elements, tagging vacated tenants with `[Vacated]` in dropdowns.
  - Added helper `isDocDateAfterVacated(docDate, tenantEndDate)` and `promptVacatedTenantConflict(tenantName, endDate, docDate)`.
  - In `submitSingleIngest`, intercepts conflict before sending or recovers from backend 400 responses by presenting the dialog.
  - In `submitHouseBatchIngest`, checks queue documents against target tenant and prompts user before queue processing.
  - Zero diff verified across all three static directories.
- **`tests/frontend/components/ingest_station.test.js`**:
  - Added unit tests for date conflict detection, modal prompt presentation, and submit action dispatching.
  - All 277 Vitest tests across 27 files pass.

## Verification
- ASP.NET Core xUnit: 148 passed (`~/.dotnet/dotnet test web-net/FileOrganizer.Tests/FileOrganizer.Tests.csproj`)
- Python Pytest: 44 passed (`.venv/bin/pytest tests/test_document_management_api.py tests/test_v14_features.py tests/test_api_v11.py`)
- Frontend Vitest: 277 passed across 27 files (`npm run test:frontend`)
- Tri-directory webroot synchronization: 0 diff verified
