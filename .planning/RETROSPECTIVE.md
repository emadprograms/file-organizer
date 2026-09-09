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
