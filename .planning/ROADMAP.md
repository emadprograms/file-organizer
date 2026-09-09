# Roadmap: File Organizer

## Milestones

- 🚧 **v12.0 Unified Document Ingestion System** — Phases 97-100 (in progress)
- ✅ **v11.0 Database Backend & Clean Storage Architecture** — Phases 92-96 (shipped 2026-09-09)
- ✅ **v10.0 Area Grid Overview & Tenure Visualization** — Phases 88-91 (shipped 2026-09-06)
- ✅ **v9.0 Hierarchical Web Dashboard** — Phases 84-87.1 (shipped 2026-09-06)
- ✅ **v8.0 Web-Based File Viewer** — Phases 81-83 (shipped 2026-09-02)

## Phases

### 🚧 v12.0 Unified Document Ingestion System (Phases 97-100)

#### Phase 97: Ingest Engine Core (Manual Ingest Pipeline & Page Inheritance)
- [x] Plan 1/1: Zero-AI manual ingest pipeline & relational page inheritance — completed 2026-09-09
**Requirements:** [ING-03, ING-04]
**Description:** Implement zero-AI manual ingestion pipeline in Python (`src/ingest/manual_ingest.py`), integrating PyMuPDF for page counting and local text extraction, storing clean batch files, saving documents directly to `vault/` with `is_manual=1`, and recording relational page inheritance in the `pages` table.
**Success Criteria:**
- Manual ingestion copies scanned files into `{house}/batches/` and `{house}/vault/`.
- Document record created with `is_manual=1` and exact page count without calling any LLM.
- Page inheritance records correctly populated in `pages` referencing batch and document.

#### Phase 98: FastAPI Ingest API Endpoints (POST /api/ingest & POST /api/ingest/preview-ai)
- [x] Plan 1/1: FastAPI Ingest API Endpoints & Preview-AI — completed 2026-09-09
**Requirements:** [API-04, API-05]
**Description:** Create FastAPI endpoints for file ingestion: `POST /api/ingest` supporting modes `manual`, `assisted`, and `auto_split`, and `POST /api/ingest/preview-ai` for single-document preview analysis before committing to storage.
**Success Criteria:**
- `POST /api/ingest` accepts multipart form upload with target house, tenant, category, subfolder, and ingestion mode.
- `POST /api/ingest/preview-ai` runs single-document preview extraction and returns suggested metadata without modifying storage.
- Proper error handling and validation for file types and missing parameters.

#### Phase 99: Ingest Station Web UI (Navbar Trigger, Dropzone & Ingest Drawer)
- [x] Plan 1/1: Ingest Station Web UI (Navbar Trigger, Dropzone & Ingest Drawer) — completed 2026-09-09
**Requirements:** [UI-01, UI-02]
**Description:** Build the Ingest Station frontend experience, featuring a top navbar `+ Ingest` button with `⌘I` / `Ctrl+I` keyboard shortcut, global/contextual drag-and-drop dropzone, slide-over drawer with PDF preview, mode switcher (`Manual`, `AI-Assisted`, `Auto-Split`), metadata form, '✨ Auto-Fill with AI', and '⚡ Ingest Directly'.
**Success Criteria:**
- Navbar button and `Cmd/Ctrl+I` shortcut trigger the Ingest Station drawer.
- Drag-and-drop dropzone highlights and loads dropped PDFs into the ingest flow.
- Slide-over drawer provides PDF preview, mode selection, form fields (House, Tenant, Folder/Category, Year), and action buttons.
- Real-time UI refresh triggers after successful ingestion without requiring page reload.

#### Phase 100: Comprehensive Automated Testing & End-to-End Verification
**Requirements:** [VER-03, VER-04]
**Description:** Build comprehensive automated test suites for both backend and frontend, including pytest integration tests for ingestion endpoints/engines and Vitest test suite for Ingest Station UI interactions.
**Success Criteria:**
- Pytest suite verifies `POST /api/ingest`, `POST /api/ingest/preview-ai`, manual ingest pipeline, and page inheritance.
- Vitest suite tests Ingest Station drawer opening, dropzone drag-and-drop, mode toggling, form submission, and UI updates.
- 100% test pass rate across backend and frontend suites.

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
| 100. Comprehensive Automated Testing & End-to-End Verification | v12.0 | 0/1 | Pending | — |

