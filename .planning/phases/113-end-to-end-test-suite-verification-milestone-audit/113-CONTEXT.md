# Phase 113: End-to-End Test Suite Verification & Milestone Audit - Context

**Gathered:** 2026-09-13
**Status:** Ready for planning
**Mode:** Autonomous execution

<domain>
## Phase Boundary

Phase 113 delivers the final verification gate and milestone audit for Milestone v15.0:
- **VER-01**: Implement backend xUnit tests covering the `is_resident` schema migration, vacancy calculation with non-residing applicants, and auto-reallocation guardrails, including end-to-end API tests in `ApiEndpointTests.cs`.
- **VER-02**: Implement frontend Vitest tests covering the segregated Tenancy Register, applicant card rendering, House Settings modal applicant row interactions, Ingest dropdown options, and dedicated end-to-end workflow verification in `applicant_workflow.test.js`.
- Milestone Lifecycle: Run milestone audit (`v15.0-MILESTONE-AUDIT.md`), milestone completion, and documentation updates.

</domain>

<decisions>
## Implementation Decisions

### 1. API-Level Backend Tests (VER-01)
- In `tests/HousingApplication.Tests/ApiEndpointTests.cs`:
  - Test `GetHouseProfile_WithResidentAndApplicant_ReturnsSegregatedProfile`: verifies `GET /api/areas/{areaId}/houses/{houseId}/profile` includes both resident and applicant tenants with correct `is_resident` flags and `active_resident`.
  - Test `BulkUpdateTenants_WithApplicant_SavesAndDoesNotReallocateDocsToApplicant`: verifies `POST /api/areas/{areaId}/houses/{houseId}/tenants` persists `is_resident: 0` and ensures reallocation bypasses applicant.
  - Test `GetTimeline_ReturnsApplicantStatus`: verifies `GET /api/areas/{areaId}/houses/{houseId}/timeline` returns `is_resident = 0` for documents belonging to applicants.
  - Test `Search_ReturnsApplicantBadgeAndNotCurrent`: verifies `GET /api/search?q=...` returns applicant search results with `is_resident = 0`, `is_current = false`, and `duration_category = null`.

### 2. Dedicated End-to-End Frontend Test Suite (VER-02)
- Create `tests/frontend/components/applicant_workflow.test.js`:
  - Test full lifecycle:
    1. Render house profile with resident and applicant: verify segregated sections, badges, and attributes.
    2. Click applicant card: verify hash routing to applicant's tenant folder.
    3. House settings modal: add new applicant row, verify disabled Present and End Date, verify submitted payload.
    4. Batch move / copy tenant select: verify applicant options are labeled with `📋` and `(متقدم - لم يسكن)`.
    5. Timeline: verify document card for applicant receives purple applicant badge.

### 3. Full Test Suite Execution
- Run `export PATH="$HOME/.dotnet:$PATH" && dotnet test HousingApplication.sln` — all tests pass (0 failures).
- Run `npm run test:frontend` — all tests pass across all test files (0 failures).

### 4. Milestone Audit & Completion
- Verify all 17 requirements (ARCH-01..05, DB-01..02, VCN-01..02, REG-01..03, SET-01, ING-01, TIM-01, VER-01..02).
- Generate `.planning/v15.0-MILESTONE-AUDIT.md`.

</decisions>

<code_context>
## Existing Code Insights

- `tests/HousingApplication.Tests/ApiEndpointTests.cs`: ASP.NET Core `WebApplicationFactory` API integration test suite.
- `tests/frontend/components/`: Vitest frontend test suites.

</code_context>

<specifics>
## Specific Requirements

- Zero regressions across existing features.
- All 17 requirements must be marked as Complete in `REQUIREMENTS.md` with 100% traceability.

</specifics>
