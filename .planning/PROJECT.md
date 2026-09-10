# File Organizer Refactoring

## What This Is

A document management system that processes scanned Arabic PDFs, categorizes them using LLM vision, groups related pages, and stores them in a high-performance relational SQLite database with a clean two-folder disk structure (`batches/` and `vault/`). The system features a responsive web dashboard with dual Tree/Grid views, tenure color-coding, multi-tenant chronological timelines, category drill-downs, phonetic/fuzzy global search, and in-browser PDF viewing.

## Current Milestone: None (v14.0 Completed & Shipped)

Milestone v14.0 Power-User Operations & Portfolio Expansion has successfully shipped. The system is fully operational with dual-backend parity across FastAPI and ASP.NET Core 8.0, comprehensive test coverage (222 tests passing), and power-user tooling. Ready for next milestone initialization.

## Past Milestones

<details>
<summary>v14.0 Power-User Operations & Portfolio Expansion (Shipped: 2026-09-10)</summary>

- Delivered one-click house archive ZIP export endpoint (`GET /api/areas/{area}/houses/{house}/export-zip`) across both FastAPI and ASP.NET Core, with UI download trigger on House Profile header.
- Implemented multi-document batch operations: per-card checkboxes, folder and global Select All toggles, floating bottom action bar (`#batch-action-bar`), atomic Batch Move, and cascade permanent Batch Delete.
- Added portfolio expansion: "+ Add House" UI modal in Area Grid overview, automatic physical directory scaffolding (`batches/`, `vault/`), SQLite registration, optional initial tenant, and live DOM grid refresh.
- Built global Keyboard Shortcuts Helper Modal (`?` / Shift+/) and navbar trigger button (`#btn-shortcuts-trigger`) with `Esc`/backdrop dismissal and text input typing isolation.
- Verified 100% test pass rate across 222 automated tests: .NET xUnit (47), Python Pytest (33), Vitest frontend (93), Playwright browser E2E (49), and zero static asset diff between `src/api/static/` and `web-net/wwwroot/`.

</details>

<details>
<summary>v13.0 Decoupled Monorepo Architecture & Native ASP.NET Core Web Server (Shipped: 2026-09-09)</summary>

- Decoupled user-facing web dashboard completely from Python runtime into ASP.NET Core 8.0 Minimal API backend (`web-net/`).
- Implemented high-performance data access layer with Dapper and `Microsoft.Data.Sqlite` in WAL mode (`organizer.db`).
- Achieved 100% JSON API parity across `/api/tree`, `/api/houses`, `/api/timeline`, `/api/categories`, `/api/tenants`, `/api/search`, and `/api/pdf/{vault_id}`.
- Zero-Python manual ingestion endpoint (`POST /api/ingest`) directly writing vault PDFs and SQLite records in .NET.
- Zero frontend rewrite: existing vanilla JS/HTML dashboard served directly from `wwwroot/` with correct MIME types.
- Generated and verified standalone self-contained Windows single-file executable (`dist/win-x64/FileOrganizer.Web.exe`) requiring zero runtime dependencies.
- Verified by 40 .NET tests, 62 pytest tests, and 61 Vitest tests (163 total passing tests).

</details>

<details>
<summary>v12.0 Unified Document Ingestion System (Shipped: 2026-09-09)</summary>

- Built zero-AI manual ingest engine with PyMuPDF page counting and instant execution (`src/ingest/manual_ingest.py`).
- Implemented relational page inheritance in SQLite `pages` table, linking batch pages with parent document metadata and `is_continuation` flag.
- Created FastAPI endpoints `POST /api/ingest` (modes: `manual`, `assisted`, `auto_split`) and `POST /api/ingest/preview-ai` with zero database or disk mutations on preview.
- Developed modern Ingest Station slide-over drawer with `⌘I` / `Ctrl+I` keyboard shortcut, fullscreen drag-and-drop dropzone, live PDF preview, mode switcher, and real-time UI refresh.
- Verified 100% test coverage across backend pytest (62 tests) and frontend Vitest (43 tests).

</details>

<details>
<summary>v11.0 Database Backend & Clean Storage Architecture (Shipped: 2026-09-09)</summary>

- Designed and implemented relational SQLite schema (`areas`, `houses`, `tenants`, `batches`, `pages`, `documents`) with WAL mode, foreign keys, cascading deletes, unique constraints, and performance indices (`src/db/`).
- Built idempotent migration pipeline (`src/migration/v11_migration.py`) restructuring legacy houses into clean `{house}/batches/` and `{house}/vault/` directories, eliminating `.lnk` shortcuts, legacy JSONs, and directory clutter.
- Redesigned multi-page scanned PDF ingestion (`src/ingest/v11_ingest.py`) to register batches and slice standalone vault PDFs directly, completely eliminating index shifting and the reconciliation loop.
- Rebuilt FastAPI backend (`/api/tree`, `/api/houses`, `/api/timeline`, `/api/categories`, `/api/search`) to execute indexed SQL queries directly in <10ms, eliminating SMB filesystem walks and memory caching overhead.
- Verified 100% feature parity with Playwright E2E UI suite (`tests/frontend/test_v11_e2e_db.py`) covering Tree View, Grid Overview, Tenure Color-Coding (<5y, 5–10y, >10y), Drill-Down, Search, and PDF previews.

</details>

<details>
<summary>v10.0 Area Grid Overview & Tenure Visualization (Shipped: 2026-09-06)</summary>

- Built dual-view toggle supporting both classic Tree View and new Area Grid Overview.
- Designed responsive house card grid featuring current resident, tenure duration, and tenure color coding (<5y green, 5-10y yellow, >10y red).
- Implemented card metrics with total document counts and category breakdowns.
- Added smooth drill-down navigation from house cards into categories and timeline views with breadcrumb return.
- Resolved SMB mount filesystem hangs with intelligent in-memory TTL caching and fast regex scanning.
- Maintained 100% test pass rate with full Playwright E2E and backend integration suites.

</details>

<details>
<summary>v9.0 Hierarchical Web Dashboard (Shipped: 2026-09-06)</summary>

- Hierarchical drill-down sidebar (Areas -> Houses -> Tenants/Timelines).
- Global search bar with Cmd/Ctrl+K, Esc, instant zero-click search dropdown.
- Arabic-English phonetic intermixing and OCR typo tolerance.
- Full-text document search inside PDF contents.
- PDF hover preview tooltips and static IIS export pipeline.
- Frontend interaction test suite.

</details>

<details>
<summary>v8.0 Web-Based File Viewer (Shipped: 2026-09-02)</summary>

- Initial web dashboard for document viewing and exploration.

</details>

## Core Value

Documents are safely stored once in an immutable vault with relational SQLite metadata, delivering sub-10ms queries, zero SMB network globbing, and an intuitive web interface for managing and reviewing multi-tenant household archives.

## Requirements

### Validated

- ✓ Full house archive ZIP export endpoint in FastAPI and ASP.NET Core (EXP-01) — v14.0
- ✓ UI Export Archive ZIP button on House Profile header with toast feedback (EXP-02) — v14.0
- ✓ Multi-select checkboxes and floating bottom action bar in category folders (BAT-01) — v14.0
- ✓ Batch Move and cascade Batch Delete endpoints in FastAPI and ASP.NET Core (BAT-02) — v14.0
- ✓ House creation backend endpoint with physical directory scaffolding (HSE-01) — v14.0
- ✓ "+ Add House" UI modal and dynamic live grid refresh in Area Grid (HSE-02) — v14.0
- ✓ Global Keyboard Shortcuts Helper Modal (`?`) and navbar trigger button (KBD-01) — v14.0
- ✓ Comprehensive multi-stack test suite across Pytest, xUnit, Vitest, Playwright (VER-07) — v14.0
- ✓ Decoupled monorepo structure (`web-net/` for ASP.NET Core, `src/` for Python AI pipeline, shared `organizer.db`) (ARCH-01) — v13.0
- ✓ ASP.NET Core 8.0 project with Dapper and `Microsoft.Data.Sqlite` in WAL mode (NET-01) — v13.0
- ✓ Port all read API endpoints with 100% JSON parity (NET-02) — v13.0
- ✓ Implement zero-Python manual ingestion endpoint (`POST /api/ingest`) in .NET (NET-03) — v13.0
- ✓ Static file serving from `wwwroot/` with existing frontend assets (NET-04) — v13.0
- ✓ API parity test suite verifying response parity between Python and .NET backends (VER-05) — v13.0
- ✓ Windows self-contained single-file publish verification (`win-x64`) (VER-06) — v13.0
- ✓ Zero-AI manual ingest pipeline in Python with PyMuPDF page counting (ING-03) — v12.0
- ✓ Relational page inheritance for manual documents in SQLite pages table (ING-04) — v12.0
- ✓ FastAPI POST /api/ingest supporting manual, assisted, auto_split modes (API-04) — v12.0
- ✓ FastAPI POST /api/ingest/preview-ai with zero mutations on preview (API-05) — v12.0
- ✓ Top navbar + Ingest button with ⌘I / Ctrl+I and drag-and-drop dropzone (UI-01) — v12.0
- ✓ Ingest Station slide-over drawer with preview, mode switcher, live refresh (UI-02) — v12.0
- ✓ Backend pytest test suite for ingest pipeline, preview, and page inheritance (VER-03) — v12.0
- ✓ Frontend Vitest test suite for Ingest Station drawer, dropzone, mode switching, form submission (VER-04) — v12.0
- ✓ SQLite schema with FKs, cascading deletes, unique constraints, and indices (DB-01) — v11.0
- ✓ Data Access Layer / Repository with connection management and transactions (DB-02) — v11.0
- ✓ Idempotent migration pipeline ingesting state.json/report.json into SQLite (MIG-01) — v11.0
- ✓ Physical disk restructuring to batches/ and vault/, removing shortcuts and legacy JSONs (MIG-02) — v11.0
- ✓ Ingestion workflow registering batches and persisting pages (ING-01) — v11.0
- ✓ Direct PDF slicing into vault/ and documents records, eliminating index shifting (ING-02) — v11.0
- ✓ Rewrite /api/tree, /api/timeline, /api/categories to query SQLite with indexed joins (API-01) — v11.0
- ✓ Fast SQLite search endpoint /api/search across houses, tenants, and documents (API-02) — v11.0
- ✓ Sub-10ms query times eliminating SMB globbing and removing memory cache workarounds (API-03) — v11.0
- ✓ Full pytest test suite covering models, repository, migration, and ingestion (VER-01) — v11.0
- ✓ Playwright E2E verification confirming Tree View, Grid Overview, Timeline, Categories, PDF viewers (VER-02) — v11.0
- ✓ Dual-view toggle supporting Tree View and Area Grid Overview (Phase 88) — v10.0
- ✓ House card grid with current resident, tenure duration, and color-coding (Phase 89) — v10.0
- ✓ Card metrics with total document counts and category breakdowns (Phase 89) — v10.0
- ✓ Smooth drill-down navigation from house cards into categories and timeline (Phase 90) — v10.0
- ✓ Playwright E2E test suite for grid view and tenure badges (Phase 91) — v10.0
- ✓ 3-level hierarchical sidebar navigation (Area -> House -> Tenant) — v9.0
- ✓ Global search across houses, tenants, and PDF contents with keyboard shortcuts — v9.0
- ✓ Arabic-English phonetic intermixing and fuzzy matching — v9.0
- ✓ Vault storage system with unique document IDs — v5.0
- ✓ Modular restructuring (core, utils, tenant_config, grouping, timeline, routing) — v2.0
- ✓ Port file-categorizer OCR and Gemini logic to main repository — v3.0

### Out of Scope

- Client-side document mutation / editing (vault PDFs are immutable).
- Complex multi-master database replication (single SQLite file with WAL mode satisfies all performance requirements).

## Current State

- ✅ Shipped v14.0 Power-User Operations & Portfolio Expansion on 2026-09-10.
- ✅ Shipped v13.0 Decoupled Monorepo Architecture & Native ASP.NET Core Web Server on 2026-09-09.
- ✅ Shipped v12.0 Unified Document Ingestion System on 2026-09-09.
- ✅ Shipped v11.0 Database Backend & Clean Storage Architecture on 2026-09-09.
- 222 tests passing across .NET xUnit (47), backend pytest (33), frontend Vitest (93), and Playwright E2E (49) test suites.
- Dual-backend runtime parity: FastAPI and ASP.NET Core 8.0 Minimal APIs running in parallel with 100% contract parity and zero static asset diff.

## Context

- The codebase has been transitioned from filesystem globbing and JSON state files to a high-performance SQLite relational database (`organizer.db`).
- Disk structure per house is simplified to `{area}/{house}/batches/` (scans) and `{area}/{house}/vault/` (sliced PDFs).
- All Windows `.lnk` shortcuts, nested Arabic directory trees, and `state.json`/`report.json` dependencies are replaced by SQLite records and fast SQL queries.

## Key Decisions

| Decision | Rationale | Outcome |
|---|---|---|
| Power-User Operations & Portfolio Expansion | Equip property managers with high-utility operations: one-click ZIP export, multi-select bulk operations, UI-based house creation, and global keyboard shortcuts. | ✓ Completed (Milestone v14.0). |
| Decoupled Monorepo & ASP.NET Core Web Server | Decouple read-heavy web dashboard into a high-efficiency native .NET 8 binary (`web-net/`) using Dapper and SQLite in WAL mode. Preserves Python strictly for offline/batch AI ingestion while giving Windows servers a zero-Python runtime footprint. | ✓ Completed (Milestone v13.0). |
| SQLite Relational Schema | Single file with WAL mode provides ACID transactions, sub-10ms query execution, and eliminates SMB directory traversal overhead. | ✓ Completed (Phase 92). |
| Two-Folder Disk Structure (`batches/` and `vault/`) | Clear separation between raw scanned inputs and sliced standalone documents. Eliminates deep Arabic directory nesting. | ✓ Completed (Phase 93). |
| Ingestion Without Reconciler | Slicing directly into `vault/` and recording in `documents` avoids index-shifting math and brittle two-way file moves. | ✓ Completed (Phase 94). |
| Direct SQL API Endpoints | Querying indexed SQLite tables instead of walking disk folders reduces tree rendering latency from seconds to <10ms. | ✓ Completed (Phase 95). |
| Playwright E2E Verification | Verifies real browser behavior against actual database records, guaranteeing zero regressions across Tree, Grid, Search, and PDF viewing. | ✓ Completed (Phase 96). |

---
*Last updated: 2026-09-09 for Milestone v13.0 initialization*
