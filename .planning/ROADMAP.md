# Roadmap: Housing Application

## Milestones

- 🟡 **v17.0 User Authentication, Roles & Permissions** — Phases 116-119 (in progress)
- ✅ **v16.1 Document-Anchored Tenancy Dates & Minimalist Register** — Phase 115 (shipped 2026-09-14)
- ✅ **v16.0 Settings Streamlining & Applicant Alignment** — Phase 114 (shipped 2026-09-13)
- ✅ **v15.0 Decoupled .NET Core Architecture & Non-Residing Applicants Archive** — Phases 109-113 (shipped 2026-09-13)
- ✅ **v14.0 Power-User Operations & Portfolio Expansion** — Phases 105-108 (shipped 2026-09-12)
- ✅ **v13.0 Decoupled Monorepo Architecture & Native ASP.NET Core Web Server** — Phases 101-104 (shipped 2026-09-09)
- ✅ **v12.0 Unified Document Ingestion System** — Phases 97-100 (shipped 2026-09-09)
- ✅ **v11.0 Database Backend & Clean Storage Architecture** — Phases 92-96 (shipped 2026-09-09)
- ✅ **v10.0 Area Grid Overview & Tenure Visualization** — Phases 88-91 (shipped 2026-09-06)
- ✅ **v9.0 Hierarchical Web Dashboard** — Phases 84-87.1 (shipped 2026-09-06)
- ✅ **v8.0 Web-Based File Viewer** — Phases 81-83 (shipped 2026-09-02)

## Phases

### 🟡 v17.0 User Authentication, Roles & Permissions (Phases 116-119)

- [ ] **Phase 116: User Data Model, Password Security & Auth API**
  - Goal: Create SQLite users table, cryptographic password hashing, seed 10 users (4 Admins: Emad, Bubshait, Ehtezaz, Mustafa; 6 Contributors: Nawaf, Naseem, Mulla, Mariam, Shaima, Mona), build session/cookie authentication endpoints (`/api/auth/login`, `/api/auth/logout`, `/api/auth/me`), and enforce backend 403 Forbidden on document/batch/page/house deletion for contributors.
  - Requirements: AUTH-01, AUTH-02, AUTH-03, AUTH-04, RBAC-01, RBAC-02, RBAC-03, RBAC-04, VER-01
- [ ] **Phase 117: Login Screen, Session Management & Navbar User Profile**
  - Goal: Implement bilingual (Arabic/English) login screen, active user session check, top navbar user indicator with avatar and role badge (`صلاحيات كاملة • Full Access` vs `قراءة ورفع فقط • Read & Upload`), and logout workflow.
  - Requirements: UI-01, UI-02, UI-03, VER-02
- [ ] **Phase 118: Permission-Aware UI Enforcement & Zero-Delete Guards**
  - Goal: Hide/disable all delete triggers across the frontend for Contributor users (3-dots menu Delete Document, multi-select Delete Selected, Document Page Editor page deletion, House Settings Danger Zone).
  - Requirements: PERM-01, PERM-02, PERM-03, PERM-04, VER-02
- [ ] **Phase 119: Comprehensive Multi-Stack Verification & Milestone Audit**
  - Goal: Run complete backend xUnit tests and frontend Vitest tests, ensure 100% static asset synchronization between `src/` and `dist/`, and audit milestone completion against requirements.
  - Requirements: VER-03

<details>
<summary>✅ v16.1 Document-Anchored Tenancy Dates & Minimalist Register (Phase 115) — SHIPPED 2026-09-14</summary>

See [.planning/milestones/v16.1-ROADMAP.md](milestones/v16.1-ROADMAP.md) for full phase details.

- [x] Phase 115: Document-Anchored Tenancy Dates & Minimalist Register (1/1 plans) — completed 2026-09-14

</details>

<details>
<summary>✅ v16.0 Settings Streamlining & Applicant Alignment (Phase 114) — SHIPPED 2026-09-13</summary>

See [.planning/milestones/v16.0-ROADMAP.md](milestones/v16.0-ROADMAP.md) for full phase details.

- [x] Phase 114: Settings Modal Simplification & Applicant Clean-Up (1/1 plans) — completed 2026-09-13

</details>

<details>
<summary>✅ v15.0 Decoupled .NET Core Architecture & Non-Residing Applicants Archive (Phases 109-113) — SHIPPED 2026-09-13</summary>

See [.planning/milestones/v15.0-ROADMAP.md](milestones/v15.0-ROADMAP.md) for full phase details.

- [x] Phase 109: Pure .NET Core Architecture & Python Elimination (1/1 plans) — completed 2026-09-13
- [x] Phase 110: Database Schema & Vacancy Guardrails for Applicants (1/1 plans) — completed 2026-09-13
- [x] Phase 111: Segregated Tenancy & Applicant Register UI (1/1 plans) — completed 2026-09-13
- [x] Phase 112: House Settings Modal & Ingestion Badging (1/1 plans) — completed 2026-09-13
- [x] Phase 113: End-to-End Test Suite Verification & Milestone Audit (1/1 plans) — completed 2026-09-13

</details>

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
| 112. House Settings Modal & Ingestion Badging | v15.0 | 1/1 | Complete | 2026-09-13 |
| 113. End-to-End Test Suite Verification & Milestone Audit | v15.0 | 1/1 | Complete | 2026-09-13 |
| 114. Settings Modal Simplification & Applicant Clean-Up | v16.0 | 1/1 | Complete | 2026-09-13 |
| 115. Document-Anchored Tenancy Dates & Minimalist Register | v16.1 | 1/1 | Complete | 2026-09-14 |
| 116. User Data Model, Password Security & Auth API | v17.0 | 0/1 | Not Started | — |
| 117. Login Screen, Session Management & Navbar User Profile | v17.0 | 0/1 | Not Started | — |
| 118. Permission-Aware UI Enforcement & Zero-Delete Guards | v17.0 | 0/1 | Not Started | — |
| 119. Comprehensive Multi-Stack Verification & Milestone Audit | v17.0 | 0/1 | Not Started | — |
