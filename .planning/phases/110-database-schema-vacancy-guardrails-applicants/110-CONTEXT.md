# Phase 110: Database Schema & Vacancy Guardrails for Applicants - Context

**Gathered:** 2026-09-13
**Status:** Ready for planning
**Mode:** Autonomous execution

<domain>
## Phase Boundary

Phase 110 delivers the database foundation and vacancy protection mechanisms for non-residing applicants and unfulfilled allocations:
- **DB-01**: SQLite schema migration adding `is_resident INTEGER NOT NULL DEFAULT 1` and `notes TEXT` to the `tenants` table with automatic idempotent column migrations for existing databases.
- **DB-02**: Update data access models (`Tenant.cs`, `TenantDto`, `HouseTenantProfileDto`, `TreeTenantDto`, `SearchResultDto`) and repository methods to read, write, and serialize `is_resident` and `notes`.
- **VCN-01**: Guard house occupancy queries (`CurrentTenant` and `DurationCategory` in `FileOrganizerRepository.cs` and `GetTreeAsync`/`GetHouseCardsAsync`/`GetHouseProfileAsync`/`SearchAsync`) so that only residing tenants (`is_resident = 1`) are considered, ensuring houses with only applicants/vacated tenants remain recognized and styled as `Vacant` (`grey`).
- **VCN-02**: Safeguard document auto-reallocation (`BulkUpdateTenantsAsync`) so date-window matching (Priority 2) and default fallback (Priority 3) only assign documents to residing tenants (`is_resident = 1`), preventing general house/utility documents from being misallocated to non-residing applicants.

</domain>

<decisions>
## Implementation Decisions

### 1. Unified Relational Table with `is_resident` Flag
- Keep applicants in the `tenants` table (`is_resident = 0`) to preserve existing relational foreign keys (`documents.tenant_id REFERENCES tenants(id)`, `pages.tenant_id REFERENCES tenants(id)`).
- This ensures applicants immediately have functional folder structures `(tenant_name, category)`, vault storage paths, and single/batch move/copy targets without creating secondary parallel tables.
- `is_resident = 1`: Default for regular residing tenants (active or past).
- `is_resident = 0`: Represents applicants, allocation order recipients who did not reside, or canceled allocations.

### 2. Idempotent Schema Migrations
- In `DatabaseInitializer.cs`:
  - Update `SchemaSql` to include `is_resident INTEGER NOT NULL DEFAULT 1` and `notes TEXT` in the `CREATE TABLE IF NOT EXISTS tenants` statement.
  - Add `CREATE INDEX IF NOT EXISTS idx_tenants_resident ON tenants(is_resident);`
  - In `InitializeSchema` and `InitializeSchemaAsync`, run `ALTER TABLE tenants ADD COLUMN is_resident INTEGER NOT NULL DEFAULT 1;` and `ALTER TABLE tenants ADD COLUMN notes TEXT;` wrapped in try/catch for `SqliteException` (handling already-existing columns).
  - Also run the same idempotent alter in `FileOrganizerRepository.EnsureSchemaAsync()`.

### 3. Model & DTO Expansion
- `Tenant.cs`: Add `public int IsResident { get; set; } = 1;` and `public string? Notes { get; set; }`.
- `TenantDto`: Add `[JsonPropertyName("is_resident")] public int IsResident { get; init; } = 1;` and `[JsonPropertyName("notes")] public string? Notes { get; init; }`.
- `HouseTenantProfileDto`: Add `[JsonPropertyName("is_resident")] public int IsResident { get; init; } = 1;` and `[JsonPropertyName("notes")] public string? Notes { get; init; }`.
- `TreeTenantDto`: Add `[JsonPropertyName("is_resident")] public int IsResident { get; init; } = 1;`.
- `SearchResultDto`: Add `[JsonPropertyName("is_resident")] public int? IsResident { get; init; }`.

### 4. Occupancy Query Guardrails (VCN-01)
- `GetTreeAsync`:
  - `activeTenant` filter must check `t.IsResident == 1`.
  - Vacant house subtitle fallback must only consider `hTenants.Where(t => t.IsResident == 1)`.
- `GetHouseCardsAsync`:
  - `activeTenant` filter must check `t.IsResident == 1`.
  - Vacant subtitle fallback must only consider `hTenants.Where(t => t.IsResident == 1)`.
- `GetHouseProfileAsync`:
  - `activeTenant` filter must check `t.IsResident == 1`.
- `SearchAsync`:
  - `CurrentTenant` subquery in houses query must include `AND is_resident = 1`.
  - For tenant search results, if `t.IsResident == 0`, `IsCurrent` must be `false` and `DurationCategory` must be `null`.

### 5. Auto-Reallocation & Ingestion Guardrails (VCN-02)
- In `BulkUpdateTenantsAsync`:
  - Support `is_resident` and `notes` in `INSERT` and `UPDATE` SQL statements.
  - When reallocating documents, filter `residentTenants = updatedTenants.Where(ut => ut.IsResident == 1).ToList()`.
  - Priority 2 (date window) and Priority 3 (default fallback) ONLY match against `residentTenants`.
  - If a house has no residing tenants, non-residing applicants are NEVER used as default fallbacks.
- In `Program.cs` document ingestion tenant resolution:
  - When resolving without explicit tenant ID or matching name, fallback to `tenants.FirstOrDefault(t => t.IsResident == 1)` first, before falling back to any tenant.

</decisions>

<code_context>
## Existing Code Insights

- `DatabaseInitializer.cs`: Initializes schema and performs idempotent column migrations.
- `FileOrganizerRepository.cs`: Contains `GetTreeAsync`, `GetHouseCardsAsync`, `GetHouseProfileAsync`, `GetTenantsAsync`, `SearchAsync`, and `BulkUpdateTenantsAsync`.
- `tests/HousingApplication.Tests/RepositoryTests.cs`: Comprehensive test suite where new unit tests for `is_resident`, vacancy styling, and auto-reallocation guardrails will be added.

</code_context>

<specifics>
## Specific Requirements

- Schema migration must not drop tables or lose data in existing databases.
- When an applicant is added with `is_resident = 0`, a house with no other active tenants MUST remain vacant (`TenureColor == "grey"` and `CurrentTenant == null`).
- General documents must never be reallocated to an applicant during bulk update reallocations.

</specifics>
