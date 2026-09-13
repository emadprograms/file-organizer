# Requirements: Housing Application (Milestone v15.0)

**Defined:** 2026-09-13
**Core Value:** A clean, high-performance, pure ASP.NET Core 8.0 web dashboard delivering sub-10ms SQLite queries, intuitive multi-tenant archive management, and strict segregation between residing tenants and non-residing applicants/unfulfilled allocations.

## v15.0 Requirements

### Clean .NET Core Architecture & Python Purge (ARCH)

- [ ] **ARCH-01**: Completely remove all legacy Python source files (`src/` Python files, `.venv/`, `requirements.txt`, `patch_index.py`, and Python pytest files in `tests/`).
- [ ] **ARCH-02**: Reorganize ASP.NET Core 8.0 project from `web-net/` into an idiomatic .NET layout: `src/HousingApplication.Web/` (with `Common/`, `Data/`, `Models/`, `wwwroot/`, `Program.cs`, `HousingApplication.Web.csproj`) and create `HousingApplication.sln`.
- [ ] **ARCH-03**: Consolidate test suites under `tests/`: Move backend tests to `tests/HousingApplication.Tests/` (linking project references to `HousingApplication.Web.csproj`) and keep frontend tests in `tests/frontend/`.
- [ ] **ARCH-04**: Update all Vitest frontend test imports across `tests/frontend/` to load static assets directly from `src/HousingApplication.Web/wwwroot/js/`, eliminating any path dependencies on legacy `src/api/static/`.
- [ ] **ARCH-05**: Update `run-mac.sh`, `package.json`, and deployment configs to reference the new project paths with zero Python dependencies, verifying that all 148 backend tests and 277 frontend tests pass 100%.

### Database Schema & Vacancy Guardrails (DB & VCN)

- [ ] **DB-01**: Update SQLite database schema across `DatabaseInitializer.cs` to add `is_resident INTEGER NOT NULL DEFAULT 1` and `notes TEXT` to the `tenants` table with automatic idempotent column migrations for existing databases.
- [ ] **DB-02**: Update data access models (`Tenant.cs`, `TenantDto`, `HouseTenantProfileDto`) and repository methods to read, write, and serialize `is_resident` and `notes`.
- [ ] **VCN-01**: Guard house occupancy queries (`CurrentTenant` and `DurationCategory` in `FileOrganizerRepository.cs`) so that only residing tenants (`is_resident = 1`) are considered, ensuring houses with only applicants/vacated tenants remain recognized and styled as `Vacant` (`grey`).
- [ ] **VCN-02**: Safeguard document auto-reallocation (`BulkUpdateTenantsAsync`) so date-window matching (Priority 2) and default fallback (Priority 3) only assign documents to residing tenants (`is_resident = 1`), preventing general house/utility documents from being misallocated to non-residing applicants.

### Segregated Tenancy & Applicant Register UI (REG)

- [ ] **REG-01**: Update House Profile (`house-profile.js`) to segregate the Tenancy Register into two distinct visual sections: **المستأجرون المقيمون** (Resident Tenants: Current with tenure colors & Past sorted by vacate date) and **سجل المتقدمين وطلبات التخصيص** (Applicants & Unfulfilled Allocations).
- [ ] **REG-02**: Implement distinctive card styling for applicants featuring an `📋 متقدم (لم يسكن)` badge, application/order date, document count, and optional notes (e.g. `ألغي التخصيص`, `لم يستلم المفتاح`).
- [ ] **REG-03**: Enable clicking an applicant's card in House Profile to navigate directly to their dedicated category folders (`03 - أمر تخصيص`, `02 - بيانات شخصية`, etc.) in Folders view.

### House Settings Modal & Ingestion Badging (SET & ING)

- [ ] **SET-01**: Update House Settings modal (`#tenant-modal` in `tenant-manager.js` and `index.html`) to support adding/editing applicants via a Resident / Applicant toggle, automatically disabling/hiding "Present" and "End Date" and relabeling "Start Date" to "Application / Order Date".
- [ ] **ING-01**: Update Ingest Station (`ingest-station.js`), Batch Move, and Batch Copy modals to clearly group or badge applicant options in tenant dropdowns (`📋 فلان (متقدم - لم يسكن)`).
- [ ] **TIM-01**: Display an applicant badge in Timeline View and Command Palette search results for documents belonging to applicants.

### Verification & Automated Testing (VER)

- [ ] **VER-01**: Implement backend xUnit tests covering the `is_resident` schema migration, vacancy calculation with non-residing applicants, and auto-reallocation guardrails.
- [ ] **VER-02**: Implement frontend Vitest tests covering the segregated Tenancy Register, applicant card rendering, House Settings modal applicant row interactions, and Ingest dropdown options.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Python runtime fallback | The web application is 100% powered by native ASP.NET Core 8.0; maintaining dual-backend parity is no longer required. |
| Automatic OCR classification of applicants | Applicant documents will be filed via manual ingestion or explicit name matching; no offline Gemini AI pipeline needed in this web app. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ARCH-01 | Phase 109 | Pending |
| ARCH-02 | Phase 109 | Pending |
| ARCH-03 | Phase 109 | Pending |
| ARCH-04 | Phase 109 | Pending |
| ARCH-05 | Phase 109 | Pending |
| DB-01 | Phase 110 | Pending |
| DB-02 | Phase 110 | Pending |
| VCN-01 | Phase 110 | Pending |
| VCN-02 | Phase 110 | Pending |
| REG-01 | Phase 111 | Pending |
| REG-02 | Phase 111 | Pending |
| REG-03 | Phase 111 | Pending |
| SET-01 | Phase 112 | Pending |
| ING-01 | Phase 112 | Pending |
| TIM-01 | Phase 112 | Pending |
| VER-01 | Phase 113 | Pending |
| VER-02 | Phase 113 | Pending |

**Coverage:**
- v15.0 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-13*
*Last updated: 2026-09-13 after v15.0 milestone start*
