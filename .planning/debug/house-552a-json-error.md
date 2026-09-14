---
status: resolved
trigger: "the thing with house 552a is that first avainash lived till 2024 september and then from october adnan loved. when i try to fix this i get json error. before you did that house. i why to understand what is happening? why can't i fix this?"
created: 2026-09-14
updated: 2026-09-14
---

## Current Focus
- hypothesis: "Deleting a removed tenant in BulkUpdateTenantsAsync executes 'DELETE FROM tenants WHERE id = @Id' before documents/pages are reallocated, violating SQLite FOREIGN KEY constraint on documents.tenant_id / pages.tenant_id, causing HTTP 500 which fails res.json() in tenant-manager.js"
- test: "Check BulkUpdateTenantsAsync order of operations, foreign key constraints, and frontend error response handling"
- expecting: "Deleting a tenant with linked documents fails foreign key check and surfaces as JSON error"
- next_action: "None. Bug is verified and resolved."

## Symptoms
1. **Expected behavior**: Removing Farid Ghazi (lawyer) and setting Avinash (until Sept 2024) and Adnan (from Oct 2024) in Tenant Manager should save successfully and reallocate documents.
2. **Actual behavior**: When saving, a "JSON error" is displayed and the changes are not persisted.
3. **Error messages**: "JSON error" (SyntaxError: Unexpected end of JSON input / unexpected token from HTTP 500 response due to SQLite Error 19: FOREIGN KEY constraint failed).
4. **Timeline**: Happens when attempting to fix house 552A in Safra D.
5. **Reproduction**: In Tenant Manager for house 552A, delete tenant Farid Ghazi (ID 270) and click Save Changes.

## Evidence
- timestamp: 2026-09-14T08:56:48Z
  observation: sqlite3 with PRAGMA foreign_keys=ON; DELETE FROM tenants WHERE id = 270; returns exit code 19: FOREIGN KEY constraint failed.
- timestamp: 2026-09-14T08:56:51Z
  observation: documents and pages tables have FOREIGN KEY (tenant_id) REFERENCES tenants(id). documents.tenant_id is NOT NULL.
- timestamp: 2026-09-14T08:56:35Z
  observation: FileOrganizerRepository.BulkUpdateTenantsAsync executes step 1 (DELETE FROM tenants WHERE id = @Id) BEFORE step 2 (insert/update) and step 3 (reallocation).
- timestamp: 2026-09-14T08:56:30Z
  observation: tenant-manager.js line 340 calls `const errData = await res.json();` without a fallback for non-JSON 500 error bodies, resulting in raw "JSON error".

## Root Cause
1. **Pipeline LLM Misattribution**: In house 552A, Avinash was sued by the Ministry of Interior for eviction. The Ministry hired external attorney Farid Ghazi Jassim Rafi (`مكتب فريد غازي جاسم رفيع`). The ingestion pipeline saw the attorney's name and created him as a resident tenant (ID 270) between Avinash and Adnan.
2. **Foreign Key Violation on Tenant Deletion**: When the user removed Farid Ghazi in the Tenant Manager modal, `BulkUpdateTenantsAsync` executed `DELETE FROM tenants WHERE id = @Id` as its first step. Because 14 documents and multiple pages were still referencing tenant 270, SQLite threw `SQLite Error 19: 'FOREIGN KEY constraint failed'`.
3. **Unprotected Frontend Error Parsing**: When ASP.NET Core returned HTTP 500, `tenant-manager.js` ran `const errData = await res.json()`, which threw `SyntaxError: Unexpected end of JSON input` because the response was empty / non-JSON, surfacing as a "JSON error" to the user.

## Fix
1. **Reordered Tenant Deletion & Document Reassignment in `BulkUpdateTenantsAsync`**:
   - Insert and update surviving tenants first.
   - For any removed tenants, reassign their documents and pages to a surviving fallback resident tenant (and reset `is_manual = 0` so date reallocation distributes them).
   - Then execute `DELETE FROM tenants WHERE id = @Id` safely without foreign key violations.
2. **Safe Frontend Error Parsing in `tenant-manager.js`**:
   - Wrap `res.json()` in try-catch with `res.text()` fallback to report human-readable error messages instead of raw JSON parse errors.
3. **API Problem Details in `Program.cs`**:
   - Wrap tenant endpoint handlers in try-catch returning `Results.Problem(detail: ex.Message, statusCode: 500)`.
4. **House 552A Data Cleaned**:
   - Tenant 270 (Farid Ghazi) deleted cleanly.
   - Tenant 269 (Avinash) configured: `2000-01-15` to `2024-09-30`.
   - Tenant 271 (Adnan) configured: `2024-10-01` to Present.
   - All court rulings and legal fees associated with Avinash's eviction lawsuit assigned to Avinash (`is_manual = 1`).
   - All October 2024+ residency documents (tenancy contract, allowance deductions, family passports, military card, electricity bills) assigned cleanly to Adnan.

## Verification
- Added 2 automated tests in `RepositoryTests.cs`:
  - `BulkUpdateTenantsAsync_WhenRemovingTenantWithDocuments_ReassignsDocumentsAndDeletesTenant`
  - `BulkUpdateTenantsAsync_WhenRemovingTenantWithDocuments_WithoutReallocate_StillReassignsDocumentsAndDeletesTenant`
- Both tests passed.
- All 166 .NET tests pass.
- All 350 Vitest frontend tests pass.
- Live API call `POST /api/areas/Safra%20D/houses/552A/tenants` succeeded with HTTP 200 `{"status":"success","reallocated_count":32,"total_documents":96,"tenants_count":2}`.
