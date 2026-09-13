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
