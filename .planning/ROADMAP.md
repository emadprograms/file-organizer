# Roadmap: File Organizer

## Milestones

- 🚧 **v13.0 Decoupled Monorepo Architecture & Native ASP.NET Core Web Server** — Phases 101-104
- ✅ **v12.0 Unified Document Ingestion System** — Phases 97-100 (shipped 2026-09-09)
- ✅ **v11.0 Database Backend & Clean Storage Architecture** — Phases 92-96 (shipped 2026-09-09)
- ✅ **v10.0 Area Grid Overview & Tenure Visualization** — Phases 88-91 (shipped 2026-09-06)
- ✅ **v9.0 Hierarchical Web Dashboard** — Phases 84-87.1 (shipped 2026-09-06)
- ✅ **v8.0 Web-Based File Viewer** — Phases 81-83 (shipped 2026-09-02)

## Phases

### 🚧 v13.0 Decoupled Monorepo Architecture & Native ASP.NET Core Web Server (Phases 101-104)

#### Phase 101: Architecture & Monorepo Restructuring Research
- [x] Plan 1/1: Architecture analysis, contract specification & project scaffolding
**Requirements:** [ARCH-01]
**Description:** Establish the decoupled monorepo boundary separating `web-net/` (ASP.NET Core 8.0 web dashboard) from `src/` (Python AI ingestion pipeline). Document the shared SQLite WAL database contract and clean storage paths (`{area}/{house}/vault/`), ensuring zero Python runtime dependency for web operations.
**Success Criteria:**
- Monorepo folder structure established with clear separation between `web-net/` and `src/`.
- Shared SQLite WAL database contract and schema mapping formally documented.
- Project scaffold for ASP.NET Core 8.0 Minimal API in `web-net/` created with modern C# project configuration.

#### Phase 102: ASP.NET Core Data Layer & Repository (Dapper + SQLite WAL)
- [x] Plan 1/1: Data access layer, SQLite connection manager & Dapper repository
**Requirements:** [NET-01]
**Description:** Implement high-performance data access layer in C# using Dapper and `Microsoft.Data.Sqlite` in WAL mode. Map models for `areas`, `houses`, `tenants`, `batches`, `pages`, and `documents`. Implement efficient read-optimized queries with connection management and transactional safety.
**Success Criteria:**
- SQLite connection factory configured with WAL journal mode, busy timeout, and connection pooling.
- Dapper repositories implemented for houses, tenants, categories, documents, and search.
- Queries execute with sub-10ms performance matching or exceeding Python SQLite benchmarks.

#### Phase 103: ASP.NET Core Minimal API Endpoints & Static Serving
- [ ] Plan 1/1: Minimal API routes, manual ingest pipeline & static asset hosting
**Requirements:** [NET-02, NET-03, NET-04]
**Description:** Build ASP.NET Core Minimal API endpoints matching Python FastAPI routes with 100% JSON parity (`/api/tree`, `/api/houses`, `/api/areas/{area}/houses/{house}`, `/api/timeline`, `/api/categories`, `/api/tenants`, `/api/search`, `/api/pdf/{vault_id}`). Implement zero-Python manual ingestion endpoint (`POST /api/ingest`). Configure static file serving from `wwwroot/` with existing vanilla JS/HTML frontend assets.
**Success Criteria:**
- All read API endpoints return exact JSON shape and status codes matching Python FastAPI.
- `POST /api/ingest` accepts manual multipart uploads, writes to vault storage, and inserts SQLite records directly in .NET.
- Existing frontend (`index.html`, `js/`, `css/`) served smoothly from `wwwroot/` with zero modifications.
- Vault PDF streaming endpoint supports byte-ranges and fast browser rendering.

#### Phase 104: Parity Verification, Windows Single-File Build & Milestone Audit
- [ ] Plan 1/1: Parity test suite, single-file win-x64 build & milestone audit
**Requirements:** [VER-05, VER-06]
**Description:** Build automated parity test suite comparing responses between Python and .NET backends across all endpoints. Verify Windows self-contained single-file publish (`win-x64`) creating `FileOrganizer.exe` for zero-dependency deployment in restricted Windows environments. Conduct milestone audit against requirements.
**Success Criteria:**
- Parity test suite passes with 100% agreement on response payloads, schema, and status codes.
- Windows self-contained single-file build succeeds (`dotnet publish -r win-x64 -c Release /p:PublishSingleFile=true /p:SelfContained=true`).
- Standalone executable runs without requiring pre-installed .NET runtime or Python environment.
- Milestone audit confirms all requirements ARCH-01, NET-01, NET-02, NET-03, NET-04, VER-05, and VER-06 are fulfilled.

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

<details>
<summary>✅ v10.0 Area Grid Overview & Tenure Visualization (Phases 88-91) — SHIPPED 2026-09-06</summary>

See [.planning/milestones/v10.0-ROADMAP.md](milestones/v10.0-ROADMAP.md) for full phase details.

</details>

<details>
<summary>✅ v9.0 Hierarchical Web Dashboard (Phases 84-87.1) — SHIPPED 2026-09-06</summary>

See [.planning/milestones/v9.0-ROADMAP.md](milestones/v9.0-ROADMAP.md) for full phase details.

</details>

<details>
<summary>✅ v8.0 Web-Based File Viewer (Phases 81-83) — SHIPPED 2026-09-02</summary>

See [.planning/milestones/v8.0-ROADMAP.md](milestones/v8.0-ROADMAP.md) for full phase details.

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|---|---|---|---|---|
| 88. View Mode Switcher & Area Grid Layout | v10.0 | 1/1 | Complete | 2026-09-06 |
| 89. House Card Metrics & Tenure Color-Coding | v10.0 | 1/1 | Complete | 2026-09-06 |
| 90. Drill-down Navigation & Static Parity | v10.0 | 1/1 | Complete | 2026-09-06 |
| 91. Playwright E2E Test Suite & Milestone Verification | v10.0 | 1/1 | Complete | 2026-09-06 |
| 92. Database Layer & Relational Schema | v11.0 | 1/1 | Complete | 2026-09-08 |
| 93. Legacy Data Migration & Storage Restructuring | v11.0 | 1/1 | Complete | 2026-09-08 |
| 94. Ingestion Pipeline Redesign | v11.0 | 1/1 | Complete | 2026-09-08 |
| 95. FastAPI High-Performance Backend | v11.0 | 1/1 | Complete | 2026-09-08 |
| 96. E2E Verification & UI Parity | v11.0 | 1/1 | Complete | 2026-09-08 |
| 97. Ingest Engine Core (Manual Ingest Pipeline & Page Inheritance) | v12.0 | 1/1 | Complete | 2026-09-09 |
| 98. FastAPI Ingest API Endpoints (POST /api/ingest & POST /api/ingest/preview-ai) | v12.0 | 1/1 | Complete | 2026-09-09 |
| 99. Ingest Station Web UI (Navbar Trigger, Dropzone & Ingest Drawer) | v12.0 | 1/1 | Complete | 2026-09-09 |
| 100. Comprehensive Automated Testing & End-to-End Verification | v12.0 | 1/1 | Complete | 2026-09-09 |
| 101. Architecture & Monorepo Restructuring Research | v13.0 | 1/1 | Complete | 2026-09-09 |
| 102. ASP.NET Core Data Layer & Repository (Dapper + SQLite WAL) | v13.0 | 1/1 | Complete | 2026-09-09 |
| 103. ASP.NET Core Minimal API Endpoints & Static Serving | v13.0 | 0/1 | Pending | - |
| 104. Parity Verification, Windows Single-File Build & Milestone Audit | v13.0 | 0/1 | Pending | - |


