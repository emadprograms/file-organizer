# Roadmap: File Organizer

## Milestones

- 🚧 **v11.0 Database Backend & Clean Storage Architecture** — Phases 92-96 (in progress)
- ✅ **v10.0 Area Grid Overview & Tenure Visualization** — Phases 88-91 (shipped 2026-09-06)
- ✅ **v9.0 Hierarchical Web Dashboard** — Phases 84-87.1 (shipped 2026-09-06)
- ✅ **v8.0 Web-Based File Viewer** — Phases 81-83 (shipped 2026-09-02)

## Phases

### 🚧 v11.0 Database Backend & Clean Storage Architecture

#### Phase 92: Database Layer & Relational Schema
**Requirements:** [DB-01, DB-02]
**Description:** Design and implement the SQLite database schema (`areas`, `houses`, `tenants`, `batches`, `pages`, `documents`), connection factory, repository functions, and comprehensive unit tests.
**Success Criteria:**
- SQLite database initializes with all tables, constraints, foreign keys, and indexes.
- Repository layer provides CRUD methods for all entities with full test coverage.
- Transactions and foreign key enforcement are strictly verified.

#### Phase 93: Legacy Data Migration & Storage Restructuring
**Requirements:** [MIG-01, MIG-02]
**Description:** Build and execute an idempotent migration script that parses `state.json`/`report.json` and reorganizes disk folders into `{area}/{house}/batches/` and `{area}/{house}/vault/`.
**Success Criteria:**
- All existing houses, tenants, batches, pages, and documents are imported into SQLite without data loss.
- Filesystem is restructured: `.lnk` shortcuts, complex Arabic directory trees, and JSON files are removed or migrated into clean two-folder structures.
- Integrity check validates 100% of vault PDFs match their database records.

#### Phase 94: Ingestion Pipeline Redesign
**Requirements:** [ING-01, ING-02]
**Description:** Refactor the ingestion engine to write raw scans into `batches`, page OCR/extractions into `pages`, slice vault PDFs, and record final items in `documents`.
**Success Criteria:**
- New PDF ingestion registers batch, creates page cache rows, groups documents, and writes directly to `documents`.
- "Prepend" mode cleanly adds new batch and page records without any index shifting on old records.
- Reconciler dependency is completely eliminated.

#### Phase 95: FastAPI High-Performance Backend
**Requirements:** [API-01, API-02, API-03]
**Description:** Rewrite FastAPI endpoints (`/api/tree`, `/api/houses`, `/api/timeline`, `/api/categories`, `/api/search`) to read directly from SQLite with indexed SQL queries.
**Success Criteria:**
- `/api/tree` and grid overview queries execute in < 10ms.
- Search endpoint queries database indexes directly instead of walking files.
- SMB globbing overhead is 100% eliminated; in-memory cache workarounds are removed.

#### Phase 96: E2E Verification & UI Parity
**Requirements:** [VER-01, VER-02]
**Description:** Run comprehensive backend unit/integration tests and Playwright E2E tests validating that Tree View, Grid Overview, Categories, Timeline, and PDF previews work seamlessly against the database.
**Success Criteria:**
- 100% test pass rate across backend pytest suite.
- Playwright E2E tests verify all UI flows, card rendering, drill-downs, and search against live SQLite database.

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
|-------|-----------|----------------|--------|-----------|
| 88. View Mode Switcher & Area Grid Layout | v10.0 | 1/1 | Complete | 2026-09-06 |
| 89. House Card Metrics & Tenure Color-Coding | v10.0 | 1/1 | Complete | 2026-09-06 |
| 90. Drill-down Navigation & Static Parity | v10.0 | 1/1 | Complete | 2026-09-06 |
| 91. Playwright E2E Test Suite & Milestone Verification | v10.0 | 1/1 | Complete | 2026-09-06 |
| 92. Database Layer & Relational Schema | v11.0 | 1/1 | Complete | 2026-09-08 |
| 93. Legacy Data Migration & Storage Restructuring | v11.0 | 0/1 | Planned | - |
| 94. Ingestion Pipeline Redesign | v11.0 | 0/1 | Planned | - |
| 95. FastAPI High-Performance Backend | v11.0 | 0/1 | Planned | - |
| 96. E2E Verification & UI Parity | v11.0 | 0/1 | Planned | - |
