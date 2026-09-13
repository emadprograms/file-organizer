---
phase: 110
plan: 110-01
status: completed
requirements_completed:
  - DB-01
  - DB-02
  - VCN-01
  - VCN-02
---

# Phase 110: Database Schema & Vacancy Guardrails for Applicants - Summary

**Execution Date:** 2026-09-13
**Status:** Completed & Verified
**Requirements Met:** DB-01, DB-02, VCN-01, VCN-02

---

## What Was Done

1. **Database Schema & Migrations (DB-01)**
   - Updated `DatabaseInitializer.SchemaSql` to add `is_resident INTEGER NOT NULL DEFAULT 1` and `notes TEXT` to the `tenants` table.
   - Added index `idx_tenants_resident ON tenants(is_resident)`.
   - Added automatic idempotent column migrations in both `InitializeSchema` and `InitializeSchemaAsync`:
     - `ALTER TABLE tenants ADD COLUMN is_resident INTEGER NOT NULL DEFAULT 1;`
     - `ALTER TABLE tenants ADD COLUMN notes TEXT;`
   - Added matching alter migrations inside `FileOrganizerRepository.EnsureSchemaAsync()`.

2. **Data Models & DTOs (DB-02)**
   - `src/HousingApplication.Web/Models/Tenant.cs`: added `IsResident` (int, default 1) and `Notes` (string?).
   - `src/HousingApplication.Web/Models/DTOs.cs`:
     - `TenantDto`: added `is_resident` (default 1) and `notes`.
     - `HouseTenantProfileDto`: added `is_resident` (default 1) and `notes`.
     - `TreeTenantDto`: added `is_resident` (default 1).
     - `SearchResultDto`: added `is_resident` (int?).

3. **Vacancy & Occupancy Guardrails (VCN-01)**
   - `GetTreeAsync`: enforces `t.IsResident == 1` when determining active resident tenant, and restricts vacant house subtitle fallback to residing tenants. Populates `IsResident` on `TreeTenantDto`.
   - `GetHousesAsync` (House cards): enforces `t.IsResident == 1` for active tenant resolution. If a house has only applicants, it is recognized as `Vacant` (`tenureColor = "grey"` and `subtitle = null`). If it had past residents, it shows the past residents' tenure range in subtitle with grey border.
   - `GetHouseProfileAsync`: enforces `t.IsResident == 1` for active resident matching. Populates `IsResident` and `Notes` on tenant profiles.
   - `GetTenantsAsync`: queries `is_resident` and `notes`, sorting residents (`is_resident = 1`) ahead of applicants (`is_resident = 0`).
   - `SearchAsync`: updated `CurrentTenant` subquery in houses query with `AND is_resident = 1`. Tenant search results for applicants have `IsCurrent = false` and `DurationCategory = null`, and map `IsResident`.

4. **Document Reallocation Guardrails (VCN-02)**
   - In `BulkUpdateTenantsAsync`:
     - Preserves and writes `is_resident` and `notes` during tenant inserts and updates.
     - In document reallocation, filters candidate targets to `residentTenants = updatedTenants.Where(ut => ut.IsResident == 1).ToList()`.
     - Date-window matching and default fallback exclusively assign documents to residing tenants. Non-residing applicants never receive auto-reallocated general documents.
   - In `Program.cs` document ingestion tenant resolution: prefers `tenants.FirstOrDefault(t => t.IsResident == 1)` before falling back to any tenant when no tenant is explicitly specified.

5. **Automated Unit Testing (VER-01)**
   - Added 6 comprehensive xUnit tests in `tests/HousingApplication.Tests/RepositoryTests.cs`:
     1. `AddTenantAsync_Applicant_SetsIsResidentZeroAndStoresNotes`
     2. `GetHouseCardsAsync_WithOnlyNonResidingApplicant_RemainsVacantGrey`
     3. `GetHouseCardsAsync_WithPastResidentAndApplicant_ShowsPastResidentSubtitleAndVacantGrey`
     4. `GetHouseProfileAsync_SegregatesActiveResidentFromApplicants`
     5. `BulkUpdateTenantsAsync_Reallocation_NeverAssignsDocsToNonResidingApplicant`
     6. `BulkUpdateTenantsAsync_PreservesApplicantStatusAndNotes`

---

## Verification Results
- **xUnit Backend Tests**: 154/154 passed (`dotnet test HousingApplication.sln`).
- **Vitest Frontend Tests**: 277/277 passed across 27 files (`npm run test:frontend`).
