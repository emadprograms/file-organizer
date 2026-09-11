# Roadmap: File Organizer

## Milestones

- ✅ **v14.0 Power-User Operations & Portfolio Expansion** — Phases 105-108 (shipped 2026-09-10)
- ✅ **v13.0 Decoupled Monorepo Architecture & Native ASP.NET Core Web Server** — Phases 101-104 (shipped 2026-09-09)
- ✅ **v12.0 Unified Document Ingestion System** — Phases 97-100 (shipped 2026-09-09)
- ✅ **v11.0 Database Backend & Clean Storage Architecture** — Phases 92-96 (shipped 2026-09-09)
- ✅ **v10.0 Area Grid Overview & Tenure Visualization** — Phases 88-91 (shipped 2026-09-06)
- ✅ **v9.0 Hierarchical Web Dashboard** — Phases 84-87.1 (shipped 2026-09-06)
- ✅ **v8.0 Web-Based File Viewer** — Phases 81-83 (shipped 2026-09-02)

## Phases

### ✅ v14.0 Power-User Operations & Portfolio Expansion (Phases 105-108) — SHIPPED 2026-09-10

- [x] Phase 105: House Archive ZIP Export Pipeline (FastAPI, ASP.NET Core & UI Button) (1/1 plans) — completed 2026-09-10
- [x] Phase 106: Multi-Select Batch Document Operations (Batch Move, Batch Delete & Selection Bar) (1/1 plans) — completed 2026-09-10
- [x] Phase 107: Portfolio Expansion ("+ Add House" Modal & Backend House Registration) (1/1 plans) — completed 2026-09-10
- [x] Phase 108: Keyboard Shortcuts Helper Modal (`?`) & Comprehensive Milestone Verification / Audit (1/1 plans) — completed 2026-09-10
- [x] Quick Refinement QCK-01: Interactive Export Options Modal (`#export-archive-modal`) & Chronological PDF Dossier Pipeline (`GET .../export-pdf`) with Tenancy Filter & 2-Digit Folder Prefix Normalization — completed 2026-09-10
- [x] Quick Refinement QCK-02: Multi-Select Batch Copy (`POST .../batch-copy`) & Timeline De-duplication Architecture (`is_timeline_visible = 0`) — completed 2026-09-10
- [x] Quick Refinement QCK-03: Descending Chronological Sort (Newest First) & Minimalist 3-Column Running Footer (Date, Category with Preserved Number, Page X/Y) — completed 2026-09-10
- [x] Quick Refinement QCK-04: Arabic Cursive Text Shaping & BiDi Visual Reordering in Exported PDF Running Footer (`arabic-reshaper` + `python-bidi` in Python, pure C# `ArabicReshaper` in .NET) — completed 2026-09-10
- [x] Quick Refinement QCK-05: Double-Click Inline Document Renaming in Categories and Timeline Views (Keyboard shortcuts Enter/Esc/Blur, Error Handling, Toast Feedback, and Backend Parity) — completed 2026-09-10
- [x] Quick Refinement QCK-06: Relocate Export Archive Button to Document Panel Header & Remove Bottom Archive Summary Box (0-scroll permanent visibility across Profile, Folders, and Timeline views) — completed 2026-09-11
- [x] Quick Refinement QCK-07: Streamline Export Modal to Intuitive Visual-First Layout & Remove Batch Button Emojis (`📁`, `📋`, `🗑️` removed, `✕ Deselect` preserved) — completed 2026-09-11
- [x] Quick Refinement QCK-08: Batch Tenant Selection in Move/Copy Modals & Remove Copy Note (Dropdown defaulting to Same Tenant, dynamic tenant loading, note removal, dual-backend support) — completed 2026-09-11
- [x] Quick Refinement QCK-09: Document 3-Dots Dropdown Action Menu & Folders Section Document Date Badge (Floating context menu with Rename, Move, Copy, Show in Timeline, Delete; always-visible date badge in folders; timeline navigation with smooth scroll & highlight) — completed 2026-09-11
- [x] Quick Refinement QCK-10: Category Folder Circular Document Count Badge & Refined Document Date Sizing (Circular count badge on folder headers; text-[9px] tracking-tight date badge on document rows) — completed 2026-09-11
- [x] Quick Refinement QCK-11: Category-Specific Folder Icons (01-13) & Empty Folder for Custom (14+) (Semantic Heroicons for 01-13; empty folder for 14+) — completed 2026-09-11
- [x] Quick Refinement QCK-12: Replace Folder "Select All" Text Button with Select Checkbox (`.folder-select-checkbox`) that Reveals Documents and Selects All — completed 2026-09-11
- [x] Quick Refinement QCK-13: Harmonize Move, Copy, and Delete Action Colors Between Multi-Select Bar and 3-Dots Dropdown Menu (Move: Amber, Copy: Indigo, Delete: Rose, Rename: Blue, Timeline: Emerald) — completed 2026-09-11
- [x] Quick Refinement QCK-14: Tenure-Based Active Tenant Colors in Tenant Selection & House Overview (Emerald green for <5 yrs, Amber yellow for 5-10 yrs, Rose red for >10 yrs matching house overview cards) — completed 2026-09-11
- [x] Quick Refinement QCK-15: Remove Redundant Emojis from Tenant Selection List and Folders Tab (Dynamic SVG Iconography) — completed 2026-09-11
- [x] Quick Refinement QCK-16: Merge Area Overview Headers into Single Top Bar & Remove Redundant Lower Header — completed 2026-09-11
- [x] Quick Refinement QCK-17: Arabic Tenant Count Badge in Tenancy Register Header (`سجل المستأجرين المتعاقبين`) — completed 2026-09-11
- [x] Quick Refinement QCK-18: Delete House Feature in Settings Modal Danger Zone (GitHub-Style Type-to-Confirm & Dual-Backend Cascade Deletion) — completed 2026-09-11
- [x] Quick Refinement QCK-19: Remove Redundant Tenancy Register Sub-Header from Tenant Selection Area (`سجل المستأجرين المتعاقبين` & count badge) — completed 2026-09-11

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
| 103. ASP.NET Core Minimal API Endpoints & Static Serving | v13.0 | 1/1 | Complete | 2026-09-09 |
| 104. Parity Verification, Windows Single-File Build & Milestone Audit | v13.0 | 1/1 | Complete | 2026-09-09 |
| 105. House Archive ZIP Export Pipeline | v14.0 | 1/1 | Complete | 2026-09-10 |
| 106. Multi-Select Batch Document Operations | v14.0 | 1/1 | Complete | 2026-09-10 |
| 107. Portfolio Expansion (+ Add House) | v14.0 | 1/1 | Complete | 2026-09-10 |
| 108. Keyboard Shortcuts & Milestone Verification | v14.0 | 1/1 | Complete | 2026-09-10 |
| QCK-01. Export Options Modal & Chronological PDF Dossier | v14.0 | 1/1 | Complete | 2026-09-10 |
| QCK-02. Multi-Select Batch Copy & Timeline De-duplication | v14.0 | 1/1 | Complete | 2026-09-10 |
| QCK-03. Descending Sort & Minimalist Running Footer Specs | v14.0 | 1/1 | Complete | 2026-09-10 |
| QCK-04. Arabic Cursive Shaping & BiDi Visual Reordering | v14.0 | 1/1 | Complete | 2026-09-10 |
| QCK-05. Double-Click Inline Document Renaming (Categories & Timeline) | v14.0 | 1/1 | Complete | 2026-09-10 |
| QCK-06. Relocate Export Archive Button to Header & Remove Archive Summary | v14.0 | 1/1 | Complete | 2026-09-11 |
| QCK-07. Streamline Export Modal & Remove Batch Button Emojis | v14.0 | 1/1 | Complete | 2026-09-11 |
