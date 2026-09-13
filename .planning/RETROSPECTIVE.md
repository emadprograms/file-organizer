# Project Retrospective

## Milestone: v11.0 — Database Backend & Clean Storage Architecture

**Shipped:** 2026-09-09
**Phases:** 5 (Phases 92–96) | **Plans:** 5 | **Tests:** 67 passed

### What Was Built
- Relational SQLite schema (`areas`, `houses`, `tenants`, `batches`, `pages`, `documents`) with foreign keys, cascading deletes, and performance indices in `src/db/`.
- Idempotent legacy migration pipeline (`src/migration/v11_migration.py`) restructuring houses into `{area}/{house}/batches/` and `{area}/{house}/vault/` while removing `.lnk` shortcuts, Arabic subfolder trees, and JSON files.
- Redesigned ingestion engine (`src/ingest/v11_ingest.py`) creating batches and slicing PDFs directly into `vault/` without index-shifting math or reconciliation loops.
- FastAPI backend endpoints (`/api/tree`, `/api/houses`, `/api/timeline`, `/api/categories`, `/api/search`) executing indexed SQL queries in < 10ms.
- Playwright E2E UI test suite (`tests/frontend/test_v11_e2e_db.py`) validating Tree View, Grid Overview, Tenure Badges (<5y, 5–10y, >10y), Drill-Down, Search, and PDF previews.

### What Worked
- Strict Test-Driven Development (TDD): writing unit, integration, and E2E tests before implementation ensured 100% test passing and zero regressions.
- Slicing vault PDFs once and storing metadata in SQLite completely eliminated the fragility and performance bottlenecks of Windows `.lnk` shortcuts and SMB filesystem directory walks.
- WAL mode SQLite provided sub-millisecond response times even when tested across network storage.

### What Was Inefficient / Resolved
- An off-by-one mismatch occurred in initial migration where 0-indexed document boundaries (`start_page: 0, end_page: 1`) were compared against 1-indexed page numbers (`p_num: 1, 2`), causing multi-page documents to shift and leaving Page 131 unlinked. This was diagnosed, caught by TDD, and resolved with boundary normalization.
- Page tenant assignment initially defaulted to tenant 1 because OCR extractions lacked expected tenant names. Resolving tenant IDs from parent document links and tenancy date ranges fixed all 131 pages.

### Key Lessons
- When ingesting legacy document archives, explicitly normalize 0-indexed vs 1-indexed page coordinates at the boundary layer.
- Relational document inheritance (`pages.vault_id -> documents.vault_id -> documents.tenant_id`) is far more reliable than heuristic OCR name matching for historical documents.

---

## Milestone: v14.0 — Power-User Operations & Portfolio Expansion

**Shipped:** 2026-09-12
**Phases:** 4 (Phases 105–108) + 42 quick refinements (QCK-01 through QCK-42) | **Plans:** 4 | **Tests:** 148 xUnit, 44 pytest, 277 Vitest across 27 files, 49 Playwright E2E passed

### What Was Built
- Full House Archive ZIP Export Pipeline with standard 2-digit folder numbering (`01 - `, `05 - `, `06 - `) and clean collision-free Arabic filenames (`{folder_index}_{title}.pdf`) across FastAPI and ASP.NET Core 8.0.
- Interactive Export Options Modal (`#export-archive-modal`) & Combined Chronological PDF Dossier (`GET /api/areas/{area}/houses/{house}/export-pdf` via PyMuPDF in Python and PdfSharpCore in .NET) with descending chronological sort, minimalist 3-column running footer, and pure C# / Python Arabic cursive shaping and BiDi visual reordering.
- Multi-Select Batch Document Operations (Batch Move, Batch Delete, Batch Copy) with glassmorphism floating action bar, target tenant reassignment, and timeline de-duplication architecture (`is_timeline_visible = 0`).
- Portfolio Expansion ("+ Add House" modal and backend physical directory scaffolding for batches and vault).
- Power-user UI refinements: double-click inline document renaming, 3-dots dropdown context menu, dynamic folder lifecycle (instant removal of 0-count folders), multi-select and touch press-and-hold drag-and-drop on tablets, full dark mode support (`Shift+D`, `theme-manager.js`), vacant house grey styling & header bar tenure legend `Vacant` indicator, vacated tenant document date conflict detection & tenancy extension prompt, and past tenants sorting by vacate date (`end_date DESC, start_date DESC`).

### What Worked
- Strict static asset synchronization across `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/` ensured 100% parity across Python and ASP.NET Core runtimes.
- Zero-motion / zero-state-shift DOM updates (`moveDocInDom`, `removeDocFromDom`, `copyDocInDom`) eliminated jarring scroll resets and accordion collapse during document moves and re-assignments.
- Pure C# `ArabicReshaper` implementation enabled standalone single-file Windows executables without external C-extension or Python dependencies.
- Multi-stack TDD (xUnit + pytest + Vitest) caught regressions across both backends and frontends before deployment.

### What Was Inefficient / Resolved
- Cross-tenant document movements within the same house initially left documents visible in the source tenant's view until manual refresh; resolved by implementing `removeDocFromDom` with folder badge and empty-state lifecycle management.
- Vacant houses with no active tenants falsely fell back to the first past tenant and calculated tenure duration as if the past tenant were still residing; resolved by eliminating the fallback, returning `ActiveTenant = null`, and introducing neutral grey styling and a `Vacant` pill badge.
- Past tenants SQL query initially ordered by `start_date DESC` instead of `end_date DESC, start_date DESC`, causing tenants with later start dates who vacated earlier to display before tenants who resided longer and vacated later; resolved across both backends.

### Patterns Established
- Dual-backend architectural symmetry: every API endpoint, schema migration, or calculation is mirrored 1:1 between FastAPI and ASP.NET Core 8.0.
- Optimistic in-place DOM updates paired with asynchronous server reconciliation.
- Pre-validation of business constraints (e.g. document date vs tenancy vacate date) at ingestion time with user-guided prompts.

### Key Lessons
- Real-world archival workflows require explicit distinction between actively residing tenants, past vacated tenants, and applicants who never resided (paving the way for Milestone v15.0).
- Early conflict detection at ingestion time prevents cumulative archive corruption.

---

## Milestone: v15.0 — Decoupled .NET Core Architecture & Non-Residing Applicants Archive

**Shipped:** 2026-09-13
**Phases:** 5 (Phases 109–113) | **Plans:** 5 | **Tests:** 158 xUnit tests, 293 Vitest tests across 28 test files (100% passing)

### What Was Built
- Completely eliminated Python runtime dependencies, transitioning repository from a dual-backend hybrid into a pure, idiomatic ASP.NET Core 8.0 Minimal API application (`src/HousingApplication.Web/` and `HousingApplication.sln`).
- Consolidated testing architecture under `tests/HousingApplication.Tests/` and updated frontend Vitest test suite (`tests/frontend/`) to import directly from `src/HousingApplication.Web/wwwroot/js/`.
- Schema additions in SQLite database (`is_resident INTEGER NOT NULL DEFAULT 1` and `notes TEXT`) with automated idempotent migrations in `DatabaseInitializer.cs`.
- Vacancy guardrails protecting house occupancy queries (`FileOrganizerRepository.cs`), ensuring houses with only non-residing applicants or unfulfilled allocations remain styled as `Vacant` (`grey`).
- Document auto-reallocation guardrails (`BulkUpdateTenantsAsync`) ensuring date-window and fallback matching strictly target resident tenants (`is_resident = 1`), preventing general property documents from being falsely assigned to applicants.
- Segregated Tenancy Register in House Profile (`house-profile.js`): split into resident tenants (current and past) vs applicants / unfulfilled allocations (`📋 متقدم (لم يسكن)`).
- Dedicated applicant folder navigation: clicking an applicant card navigates into their tenant folders (`03 - أمر تخصيص`, `02 - بيانات شخصية`, etc.).
- House Settings modal toggle (`#tenant-modal` in `tenant-manager.js`): dynamic Resident / Applicant selection that automatically hides/disables "Present" and "End Date" fields and relabels "Start Date" to "Application / Order Date".
- Visual applicant badging across Ingest Station, Batch Move, and Batch Copy dropdowns (`📋 فلان (متقدم - لم يسكن)`), as well as Timeline view and Command Palette search results.
- Comprehensive test suites verifying schema migration, vacancy calculation, auto-reallocation guardrails, and segregated UI interactions.

### What Worked
- Reusing the existing `tenants` table with an `is_resident` discriminator instead of introducing a separate `applicants` table minimized foreign key churn and kept category folder routing 100% consistent across both types of entities.
- Direct Vitest testing against real browser DOM mocks (`jsdom`) allowed rapid verification of complex modal and UI state changes without needing full browser automation.
- Transitioning to pure .NET 8.0 simplified the local development environment, build scripts (`run-mac.sh`), and CI dependencies by removing the Python virtual environment and multiple runtime synchronizations.

### What Was Inefficient
- Dual-backend maintenance in earlier milestones had accumulated redundant scripts (`patch_index.py`, dual static copies in `src/api/static/` vs `web-net/wwwroot/`) which required careful cleanup and import path re-pointing across 28 Vitest files.
- Manual verification of Arabic text alignment and RTL badge rendering required iterative inspection of DOM elements across various viewport widths.

### Patterns Established
- Single-Stack Minimal API: ASP.NET Core 8.0 Minimal API + Dapper + SQLite WAL mode as the definitive standard for local/internal archival systems.
- Discriminator-based entity specialization (`is_resident` flag) preserving unified relational hierarchies while enabling strict domain-level business filtering.
- Domain-isolated auto-reallocation: automated heuristics strictly filter on resident status to avoid corrupting applicant portfolios.

### Key Lessons
- Purging deprecated runtimes early reduces cognitive load and test suite duplication.
- Domain rules (like whether an applicant counts as a resident or affects house vacancy) must be enforced at both the database query level and the client presentation layer.

### Cost Observations
- Fast iterative phase execution: 5 focused phases completed cleanly within 1 day.
- Zero external runtime overhead; instantaneous local compilation and test execution under `dotnet test` and `vitest`.

---

## Cross-Milestone Trends

| Milestone | Architecture | Backend | Frontend Tests | Backend Tests | Python Dependency |
|---|---|---|---|---|---|
| v11.0 | Relational SQLite + FastAPI | Python | E2E (Playwright) | 67 Pytest | Yes |
| v13.0 | Decoupled Monorepo | Python + ASP.NET Core | 61 Vitest | 40 xUnit, 62 Pytest | Yes |
| v14.0 | Dual-Backend Parity | Python + ASP.NET Core | 277 Vitest (27 files) | 148 xUnit, 44 Pytest | Yes |
| v15.0 | Pure .NET Core Single-Stack | ASP.NET Core 8.0 Minimal API | 293 Vitest (28 files) | 158 xUnit | None (0%) |
