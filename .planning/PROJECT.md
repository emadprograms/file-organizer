# File Organizer Refactoring

## What This Is

A document management system that processes scanned Arabic PDFs, categorizes them using LLM vision, groups related pages, and stores them in a high-performance relational SQLite database with a clean two-folder disk structure (`batches/` and `vault/`). The system features a responsive web dashboard with dual Tree/Grid views, tenure color-coding, multi-tenant chronological timelines, category drill-downs, phonetic/fuzzy global search, and in-browser PDF viewing.

## Past Milestones

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

## Current Milestone: v12.0 Unified Document Ingestion System

- Zero-AI manual ingest pipeline storing clean batches, documents with `is_manual=1`, and page inheritance.
- FastAPI endpoints: `POST /api/ingest` and `POST /api/ingest/preview-ai`.
- Modern UI Ingest Station (navbar button, contextual drag-and-drop, slide-over drawer, single doc vs multi-doc split, real-time UI refresh).
- Full test coverage (backend pytest & frontend vitest).

## Current State

- ✅ Shipped v11.0 Database Backend & Clean Storage Architecture on 2026-09-09.
- 67 tests passing across the complete pytest backend and Playwright frontend test suite.
- House 500 cleanly migrated and verified against real disk storage with 100% data integrity.
- Web dashboard running on FastAPI with sub-10ms response times.

## Context

- The codebase has been transitioned from filesystem globbing and JSON state files to a high-performance SQLite relational database (`organizer.db`).
- Disk structure per house is simplified to `{area}/{house}/batches/` (scans) and `{area}/{house}/vault/` (sliced PDFs).
- All Windows `.lnk` shortcuts, nested Arabic directory trees, and `state.json`/`report.json` dependencies are replaced by SQLite records and fast SQL queries.

## Key Decisions

| Decision | Rationale | Outcome |
|---|---|---|
| SQLite Relational Schema | Single file with WAL mode provides ACID transactions, sub-10ms query execution, and eliminates SMB directory traversal overhead. | ✓ Completed (Phase 92). |
| Two-Folder Disk Structure (`batches/` and `vault/`) | Clear separation between raw scanned inputs and sliced standalone documents. Eliminates deep Arabic directory nesting. | ✓ Completed (Phase 93). |
| Ingestion Without Reconciler | Slicing directly into `vault/` and recording in `documents` avoids index-shifting math and brittle two-way file moves. | ✓ Completed (Phase 94). |
| Direct SQL API Endpoints | Querying indexed SQLite tables instead of walking disk folders reduces tree rendering latency from seconds to <10ms. | ✓ Completed (Phase 95). |
| Playwright E2E Verification | Verifies real browser behavior against actual database records, guaranteeing zero regressions across Tree, Grid, Search, and PDF viewing. | ✓ Completed (Phase 96). |

---
*Last updated: 2026-09-09 for v12.0 milestone initialization*
