---
phase: 110
status: passed
verified_at: "2026-09-13T20:54:00.000Z"
score: 4/4
---

# Phase 110 Verification: Database Schema & Vacancy Guardrails for Applicants

## Requirements Verification Matrix

| Requirement | Description | Status | Verification Method |
|-------------|-------------|--------|---------------------|
| **DB-01** | SQLite schema updated with `is_resident INTEGER NOT NULL DEFAULT 1` and `notes TEXT` with auto-migration | Passed | Verified by `TenantsSchema_IncludesIsResidentAndNotes_DefaultValues` and `EnsureSchemaAsync` migrations |
| **DB-02** | Data models, DTOs, and repository methods read, write, and serialize `is_resident` and `notes` | Passed | Verified by `AddTenantAsync_Applicant_SetsIsResidentZeroAndStoresNotes`, `BulkUpdateTenantsAsync_PreservesApplicantStatusAndNotes` |
| **VCN-01** | Occupancy subqueries and active tenant resolution strictly filter `is_resident = 1`, keeping houses with only applicants vacant (`grey`) | Passed | Verified by `GetHouseCardsAsync_WithOnlyNonResidingApplicant_RemainsVacantGrey` and `GetHouseCardsAsync_WithPastResidentAndApplicant_ShowsPastResidentSubtitleAndVacantGrey` |
| **VCN-02** | Auto-reallocation ignores non-residing applicants for date-window and default fallback matching | Passed | Verified by `BulkUpdateTenantsAsync_Reallocation_NeverAssignsDocsToNonResidingApplicant` |

## Test Suite Summary
- **Backend xUnit Suite**: 154 passed, 0 failed, 0 skipped.
- **Frontend Vitest Suite**: 277 passed, 0 failed, 0 skipped across 27 files.
- **Regression Check**: Zero broken endpoints or tests.
