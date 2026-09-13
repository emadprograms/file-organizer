# Roadmap: Housing Application

## Milestones

- 🔄 **v15.0 Decoupled .NET Core Architecture & Non-Residing Applicants Archive** — Phases 109-113 (in progress)
- ✅ **v14.0 Power-User Operations & Portfolio Expansion** — Phases 105-108 (shipped 2026-09-12)
- ✅ **v13.0 Decoupled Monorepo Architecture & Native ASP.NET Core Web Server** — Phases 101-104 (shipped 2026-09-09)
- ✅ **v12.0 Unified Document Ingestion System** — Phases 97-100 (shipped 2026-09-09)
- ✅ **v11.0 Database Backend & Clean Storage Architecture** — Phases 92-96 (shipped 2026-09-09)
- ✅ **v10.0 Area Grid Overview & Tenure Visualization** — Phases 88-91 (shipped 2026-09-06)
- ✅ **v9.0 Hierarchical Web Dashboard** — Phases 84-87.1 (shipped 2026-09-06)
- ✅ **v8.0 Web-Based File Viewer** — Phases 81-83 (shipped 2026-09-02)

## Phases

### 🔄 v15.0 Decoupled .NET Core Architecture & Non-Residing Applicants Archive (Phases 109-113)

- [x] Phase 109: Pure .NET Core Architecture & Python Elimination (1/1 plans) — completed 2026-09-13
- [x] Phase 110: Database Schema & Vacancy Guardrails for Applicants (1/1 plans) — completed 2026-09-13
- [x] Phase 111: Segregated Tenancy & Applicant Register UI (1/1 plans) — completed 2026-09-13
- [ ] Phase 112: House Settings Modal & Ingestion Badging (0/1 plans)
- [ ] Phase 113: End-to-End Test Suite Verification & Milestone Audit (0/1 plans)

## Phase Details

### Phase 109: Pure .NET Core Architecture & Python Elimination
- **Goal**: Remove Python dependencies, migrate ASP.NET Core project from `web-net/` to `src/HousingApplication.Web/` with `HousingApplication.sln`, consolidate tests under `tests/`, point Vitest imports to the real web root, update `run-mac.sh` and `package.json`, and verify all existing tests pass with zero Python runtime.
- **Requirements**: ARCH-01, ARCH-02, ARCH-03, ARCH-04, ARCH-05
- **Success Criteria**:
  1. Python source files (`src/` Python, `.venv`, `requirements.txt`) completely removed.
  2. ASP.NET Core project cleanly builds under `src/HousingApplication.Web/` and runs via `dotnet run`.
  3. 148 backend xUnit tests pass under `tests/HousingApplication.Tests/`.
  4. 277 frontend Vitest tests pass importing directly from `src/HousingApplication.Web/wwwroot/js/`.

### Phase 110: Database Schema & Vacancy Guardrails for Applicants
- **Goal**: Add `is_resident` and `notes` to `tenants` table with automatic migrations; protect occupancy queries so applicants never turn vacant houses into occupied houses; guard auto-reallocation to only assign general documents to residents.
- **Requirements**: DB-01, DB-02, VCN-01, VCN-02
- **Success Criteria**:
  1. SQLite schema updated with `is_resident INTEGER NOT NULL DEFAULT 1` and `notes TEXT` with auto-migration.
  2. Data models, DTOs, and repository queries updated and serialized across API endpoints.
  3. Occupancy subquery strictly filters `is_resident = 1`, ensuring houses with only applicants/vacated tenants remain styled as `Vacant` (`grey`).
  4. Auto-reallocation ignores non-residing applicants for date-window and default fallback.

### Phase 111: Segregated Tenancy & Applicant Register UI
- **Goal**: Split the House Profile register into resident tenants and applicants/unfulfilled allocations; implement applicant card styling with dates, document counts, and notes; enable clicking applicant cards to open their dedicated category folders.
- **Requirements**: REG-01, REG-02, REG-03
- **Success Criteria**:
  1. House Profile displays two distinct sections: "المستأجرون المقيمون" and "سجل المتقدمين وطلبات التخصيص".
  2. Applicant cards render with distinctive badge `📋 متقدم (لم يسكن)`, application date, document count, and notes.
  3. Clicking an applicant navigates into their folders view, displaying only their documents.

### Phase 112: House Settings Modal & Ingestion Badging
- **Goal**: Allow adding/editing applicants in House Settings modal without false residency dates; badge applicants clearly in Ingest Station and batch move/copy dropdowns; badge applicant documents in Timeline and Search.
- **Requirements**: SET-01, ING-01, TIM-01
- **Success Criteria**:
  1. House Settings modal supports toggling between Resident and Applicant, dynamically hiding Present/End Date for applicants.
  2. Ingest Station and batch modals clearly badge applicant options in tenant select dropdowns.
  3. Timeline View and Command Palette display an applicant badge for applicant documents.

### Phase 113: End-to-End Test Suite Verification & Milestone Audit
- **Goal**: Create comprehensive automated xUnit backend tests and Vitest frontend tests verifying applicant handling, vacancy states, modal workflows, and folder navigation, followed by a full milestone audit.
- **Requirements**: VER-01, VER-02
- **Success Criteria**:
  1. New xUnit tests verifying `is_resident` migrations, vacancy calculations, and reallocation guardrails.
  2. New Vitest tests verifying segregated register rendering, applicant card clicks, and modal toggles.
  3. 100% test pass rate across backend and frontend suites.

---

<details>
<summary>✅ v14.0 Power-User Operations & Portfolio Expansion (Phases 105-108) — SHIPPED 2026-09-12</summary>

See [.planning/milestones/v14.0-ROADMAP.md](milestones/v14.0-ROADMAP.md) for full phase details.

- [x] Phase 105: House Archive ZIP Export Pipeline (FastAPI, ASP.NET Core & UI Button) (1/1 plans) — completed 2026-09-10
- [x] Phase 106: Multi-Select Batch Document Operations (Batch Move, Batch Delete & Selection Bar) (1/1 plans) — completed 2026-09-10
- [x] Phase 107: Portfolio Expansion ("+ Add House" Modal & Backend House Registration) (1/1 plans) — completed 2026-09-10
- [x] Phase 108: Keyboard Shortcuts Helper Modal (`?`) & Comprehensive Milestone Verification / Audit (1/1 plans) — completed 2026-09-10
- [x] Quick Refinements QCK-01 through QCK-42 — completed 2026-09-12

</details>

<details>
<summary>✅ v13.0 Decoupled Monorepo Architecture & Native ASP.NET Core Web Server (Phases 101-104) — SHIPPED 2026-09-09</summary>

See [.planning/milestones/v13.0-ROADMAP.md](milestones/v13.0-ROADMAP.md) for full phase details.

- [x] Phase 101: Architecture & Monorepo Restructuring Research (1/1 plan) — completed 2026-09-09
- [x] Phase 102: ASP.NET Core Data Layer & Repository (Dapper + SQLite WAL) (1/1 plan) — completed 2026-09-09
- [x] Phase 103: ASP.NET Core Minimal API Endpoints & Static Serving (1/1 plan) — completed 2026-09-09
- [x] Phase 104: Parity Verification, Windows Single-File Build & Milestone Audit (1/1 plan) — completed 2026-09-09

</details>

<details>
<summary>✅ v12.0 Unified Document Ingestion System (Phases 97-100) — SHIPPED 2026-09-09</summary>

See [.planning/milestones/v12.0-ROADMAP.md](milestones/v12.0-ROADMAP.md) for full phase details.

- [x] Phase 97: Ingest Engine Core (Manual Ingest Pipeline & Page Inheritance) (1/1 plan) — completed 2026-09-09
- [x] Phase 98: FastAPI Ingest API Endpoints (POST /api/ingest & POST /api/ingest/preview-ai) (1/1 plan) — completed 2026-09-09
- [x] Phase 99: Ingest Station Web UI (Navbar Trigger, Dropzone & Ingest Drawer) (1/1 plan) — completed 2026-09-09
- [x] Phase 100: Comprehensive Automated Testing & End-to-End Verification (1/1 plan) — completed 2026-09-09

</details>

<details>
<summary>✅ v11.0 Database Backend & Clean Storage Architecture (Phases 92-96) — SHIPPED 2026-09-09</summary>

See [.planning/milestones/v11.0-ROADMAP.md](milestones/v11.0-ROADMAP.md) for full phase details.

- [x] Phase 92: Database Layer & Relational Schema (1/1 plan) — completed 2026-09-08
- [x] Phase 93: Legacy Data Migration & Storage Restructuring (1/1 plan) — completed 2026-09-08
- [x] Phase 94: Ingestion Pipeline Redesign (1/1 plan) — completed 2026-09-08
- [x] Phase 95: FastAPI High-Performance Backend (1/1 plan) — completed 2026-09-08
- [x] Phase 96: E2E Verification & UI Parity (1/1 plan) — completed 2026-09-08

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|---|---|---|---|---|
| 109. Pure .NET Core Architecture & Python Elimination | v15.0 | 1/1 | Complete | 2026-09-13 |
| 110. Database Schema & Vacancy Guardrails for Applicants | v15.0 | 1/1 | Complete | 2026-09-13 |
| 111. Segregated Tenancy & Applicant Register UI | v15.0 | 1/1 | Complete | 2026-09-13 |
| 112. House Settings Modal & Ingestion Badging | v15.0 | 0/1 | Pending | - |
| 113. End-to-End Test Suite Verification & Milestone Audit | v15.0 | 0/1 | Pending | - |
