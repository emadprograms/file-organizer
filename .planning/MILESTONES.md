# Milestones History

## v14.0 Power-User Operations & Portfolio Expansion (Shipped: 2026-09-10)

**Phases completed:** 4 phases (105-108), 4 plans, 222 tests passing (47 .NET, 33 pytest, 93 Vitest, 49 Playwright)

**Key accomplishments:**

- Full House Archive ZIP Export pipeline (`GET /api/areas/{area}/houses/{house}/export-zip`) in both FastAPI and ASP.NET Core Minimal APIs, packaging vault documents into collision-free structured ZIPs with clean Arabic filenames.
- Modern UI Export Archive ZIP button on the House Profile header with active loading spinner, client-side download initiation, and user toast notifications.
- Multi-document batch operations with selection checkboxes, folder-level & global Select All toggles, and floating bottom action bar (`#batch-action-bar`).
- Atomic Batch Move (`POST .../documents/batch-move`) and cascade permanent Batch Delete (`POST .../documents/batch-delete`) endpoints in both Python and C#.
- Portfolio expansion via "+ Add House" UI modal in the Area Grid overview with automatic physical directory scaffolding (`batches/`, `vault/`), SQLite registration, optional initial tenant, and live DOM grid refresh without page reload.
- Global Keyboard Shortcuts Helper Modal (`?` / Shift+/) and navbar trigger button (`#btn-shortcuts-trigger`) with full `Esc`/backdrop dismissal and strict exclusion of input fields.
- 100% test pass rate across all 4 suites: Pytest (33), .NET xUnit (47), Vitest (93), and Playwright browser E2E (49) with zero static asset diff.

---

## v13.0 Decoupled Monorepo Architecture & Native ASP.NET Core Web Server (Shipped: 2026-09-09)

**Phases completed:** 4 phases (101-104), 4 plans, 163 tests passing (40 .NET, 62 pytest, 61 Vitest)

**Key accomplishments:**

- Decoupled monorepo architecture establishing `web-net/` (ASP.NET Core 8.0 Minimal API) and `src/` (Python AI pipeline), with zero Python runtime dependency for web serving or manual ingestion.
- High-performance C# data layer using Dapper and `Microsoft.Data.Sqlite` in WAL mode with connection pooling, transactional integrity, and sub-10ms queries.
- Complete Minimal API endpoint suite matching Python FastAPI routes with 100% JSON parity (`/api/tree`, `/api/houses`, `/api/timeline`, `/api/categories`, `/api/tenants`, `/api/search`, `/api/pdf/{vault_id}`).
- Zero-Python manual ingestion endpoint (`POST /api/ingest`) directly writing vault PDFs and SQLite records in .NET.
- Zero-frontend rewrite serving vanilla JS/HTML assets from `wwwroot/` with correct MIME types.
- Comprehensive API parity test suite (`ParityVerificationTests.cs`) verifying response schemas, model mapping, and static assets.
- Self-contained Windows single-file publish (`dist/win-x64/FileOrganizer.Web.exe`) with IIS In-Process `web.config` and production deployment guide (`DEPLOYMENT-WINDOWS.md`).

---

## v12.0 Unified Document Ingestion System (Shipped: 2026-09-09)

**Phases completed:** 4 phases (97-100), 4 plans, 105 tests passing (62 backend, 43 frontend)

**Key accomplishments:**

- Zero-AI manual ingest engine with PyMuPDF page counting and instant execution (`src/ingest/manual_ingest.py`).
- Relational page inheritance pattern in SQLite `pages` table, linking batch pages to newly created documents with `is_continuation` properly set.
- FastAPI `POST /api/ingest` (multi-mode: manual, assisted, auto_split) and `POST /api/ingest/preview-ai` with zero database or filesystem mutations on preview.
- Modern Ingest Station slide-over drawer with `⌘I` shortcut, fullscreen drag-and-drop dropzone, PDF preview, mode switcher, and live refresh.
- 100% passing test suite across backend (pytest) and frontend (Vitest).

---

## v11.0 Database Backend & Clean Storage Architecture (Shipped: 2026-09-09)

**Phases completed:** 5 phases (92-96), 5 plans, 67 tests passing

**Key accomplishments:**

- Designed and implemented the relational SQLite schema (`areas`, `houses`, `tenants`, `batches`, `pages`, `documents`) with WAL mode, foreign keys, cascading deletes, unique constraints, and performance indices in `src/db/`.
- Built an idempotent migration engine (`src/migration/v11_migration.py`) restructuring legacy houses into clean `{house}/batches/` and `{house}/vault/` structures, eliminating `.lnk` shortcuts, legacy JSONs, and directory clutter.
- Redesigned multi-page scanned PDF ingestion (`src/ingest/v11_ingest.py`) to register batches and slice standalone vault PDFs directly, completely eliminating index shifting and the reconciliation loop.
- Rebuilt the FastAPI backend (`/api/tree`, `/api/houses`, `/api/timeline`, `/api/categories`, `/api/search`) to execute indexed SQL queries directly in <10ms, eliminating SMB filesystem walks and memory caching overhead.
- Established comprehensive Playwright E2E UI test suite (`tests/frontend/test_v11_e2e_db.py`) verifying 100% feature parity for Tree View, Area Grid Overview, Tenure Color-Coding (<5y, 5–10y, >10y), Drill-Down, Search, and PDF previews.
- Verified live migration integrity against real house data (House 500: 3 historical tenants, 65 vault docs, 131 pages accurately mapped with 0 unlinked pages).

---

## v10.0 Area Grid Overview & Tenure Visualization (Shipped: 2026-09-06)

**Phases completed:** 4 phases (88-91)

**Key accomplishments:**

- Built dual-view toggle supporting both classic Tree View and new Area Grid Overview.
- Designed responsive house card grid featuring current resident, tenure duration, and tenure color coding (<5y green, 5-10y yellow, >10y red).
- Implemented card metrics with total document counts and category breakdowns.
- Added smooth drill-down navigation from house cards into categories and timeline views with breadcrumb return.
- Resolved SMB mount filesystem hangs with intelligent in-memory TTL caching and fast regex scanning.
- Maintained 100% test pass rate with full Playwright E2E and backend integration suites.

---

## v9.0 Hierarchical Web Dashboard (Shipped: 2026-09-06)

**Phases completed:** 5 phases, 5 plans

**Key accomplishments:**

- Implemented 3-level hierarchical sidebar navigation (Area -> House -> Tenant) with deep URL linking and synchronized active node selection.
- Developed global search across houses, tenants, and full-text PDF documents with instant zero-click search dropdown and keyboard shortcuts (`Cmd/Ctrl+K`, `Esc`).
- Added Arabic-English phonetic intermixing and fuzzy matching for Arabic OCR names.
- Enhanced document viewer with PDF hover preview tooltips and tabbed Category / Timeline views.
- Created static IIS export pipeline (`tree.json`, `search_index.json`) for zero-Python runtime environments.
- Built comprehensive interaction test suite in `tests/frontend/`.

---

## v8.0 Web-Based File Viewer (Shipped: 2026-09-02)

**Phases completed:** 4 phases, 3 plans, 0 tasks

**Key accomplishments:**

- (none recorded)

---

## v5.2: Deep Architecture Integrity & Verification

**Shipped:** 2026-08-01

**Key Accomplishments:**

- Created robust `src/core/verification.py` module to deep-scan houses for file system integrity.
- Handled legacy artifacts, orphan vault files, missing shortcuts, and state vs. physical folder drift securely.
- Resolved tricky cross-platform edge cases involving Pytest mocked environments, `pylnk3`, and Windows long paths.
- Reached 100% passing test coverage (288 tests) across the entire system.

## v5.1: Polishing & Migration Cleanup

**Shipped:** 2026-08-01

**Key Accomplishments:**

- Unified `1_cleaned.json`, `2_grouped.json`, and `3_routed_and_finalized.json` into a single `state.json` file.
- Fixed the Timeline View document index numbering logic to properly jump indices relative to document page count.
- Expanded automated test coverage by refactoring tests away from legacy formats and creating `tests/test_live_e2e.py` targeting actual test sets.
- Fixed `pylnk3` Windows dependency resolution.
