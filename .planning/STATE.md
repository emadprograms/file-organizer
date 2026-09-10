---
gsd_state_version: 1.0
milestone: v13.0
milestone_name: Decoupled Monorepo Architecture & Native ASP.NET Core Web Server
current_phase: 104
status: completed
last_updated: "2026-09-09T18:40:00.000Z"
last_activity: 2026-09-09
last_activity_desc: "Completed Phase 104: Parity Verification, Windows Single-File Build & Milestone Audit. Milestone v13.0 Shipped."
progress:
  total_phases: 4
  completed_phases: 4
  total_plans: 4
  completed_plans: 4
  percent: 100
stopped_at: Completed Phase 104 & Shipped Milestone v13.0
---

# Milestone State

**Current Milestone:** v13.0: Decoupled Monorepo Architecture & Native ASP.NET Core Web Server (Shipped: 2026-09-09)
**Current Phase:** 104: Parity Verification, Windows Single-File Build & Milestone Audit (Completed)
**Status:** completed


## Context

Decoupling the lightweight web dashboard/UI completely from the Python AI batch ingestion pipeline. The web server will be an ASP.NET Core 8.0 Minimal API application in `web-net/`, sharing only `organizer.db` (SQLite in WAL mode) and the clean disk vault (`{area}/{house}/vault/`). The existing vanilla JS/HTML frontend remains 100% identical and is served from `wwwroot/`. The Python pipeline remains in `src/` for offline/batch AI processing.

## Target Phases

- Phase 101: Architecture & Monorepo Restructuring Research (Completed)
- Phase 102: ASP.NET Core Data Layer & Repository (Dapper + SQLite WAL)
- Phase 103: ASP.NET Core Minimal API Endpoints & Static Serving
- Phase 104: Parity Verification, Windows Single-File Build & Milestone Audit

## Quick Tasks Completed

- `260909-3b2`: UI-Based Tenant Management & Document Reallocation (with unit tests in `test_tenant_repository_unit.py`, API tests in `test_tenant_reallocation_api.py`, and Playwright E2E tests in `test_v11_e2e_db.py`).
- `260909-405`: Modern UI Layout Overhaul, Settings Button Placement & Lucide-style Iconography (all 65 backend and frontend tests passed).
- `260909-doc-management-move-copy-rename`: Safe UI-Based Document Management (Rename, Move/Copy Folder, Tenant Reassign, Permanent Manual Lock, Sequential Custom Folders; 7 API tests in `test_document_management_api.py` and 5 Playwright E2E tests in `test_v11_e2e_db.py`).
- `260909-spotlight-search-and-modularize-ui`: macOS Spotlight Command Palette (`⌘K`) with section grouping (Houses, Tenants, Documents), full breadcrumbs (`Area › House › Tenant › Folder`), keyboard navigation (`↑`/`↓`/`Enter`/`Esc`), and `index.html` refactoring (~2,400 to ~500 lines) with 5 modular JS files. 17 frontend Playwright E2E tests and 30 backend tests passing.
- `260909-house-tenancy-register-and-archive-profile`: Arabic House Tenancy Register (`سجل المستأجرين المتعاقبين`) & Digital Archive Profile (`بيانات الأرشيف الرقمي للمنزل`). Clicking a house renders the tenancy register with active/past tenant cards, tenure duration, document counts, and archive stats. Clicking a tenant card or tree node drills down into that tenant's category folders with a `← سجل المنزل` back button. Verified by 2 new backend tests and 2 new Playwright E2E tests; all 52 frontend and 59 backend tests passing.
- `260909-remove-tree-view-and-enhance-tenants-overview`: Remove tree view entirely, make houses overview default, short tenants overview on cards, and intuitive back-to-tenants navigation (`#back-to-tenants-btn` and category banner). All 90 frontend and backend tests passing.
- `260909-gnj`: Non-Intrusive PDF Preview & macOS Spacebar Quick Look. Made hover preview strictly non-blocking (`pointer-events: none`), anchored positioning without cursor chasing, decoupled preview trigger to document icon only, suppressed preview on 3-dot menu hover/click, and added full native macOS Spacebar Quick Look modal with keyboard navigation. All 22 Vitest frontend and 19 pytest backend tests passing.
- `260909-h90`: Right Panel Live Peek on Hover & macOS Spacebar Quick Look. Zero-click ambient live peek directly in the right panel on hover (250ms debounce), removed all floating tooltips from over the list, preserved centered macOS Spacebar Quick Look modal and Eye button, and ensured 3-dot menus are 100% unobstructed. All 24 Vitest frontend and 19 pytest backend tests passing.
- `260910-user-batch-filing-and-remove-ai-frontend`: Multi-File Batch Filing & Complete AI Removal from Frontend. Removed all AI autofill buttons, labels, and `/api/ingest/preview-ai` calls from frontend for 100% deterministic operation. Implemented multi-file batch queue with editable titles, auto-detected house numbers, auto-selected latest tenants, single document broadcasting across multiple houses (`+ Add House`), and sequential `POST /api/ingest` execution with live progress tracking. 68 Vitest tests, 4 Playwright E2E tests, 12 backend API tests, and 40 .NET tests passing.

## Current Position

Phase: Phase 104: Parity Verification, Windows Single-File Build & Milestone Audit (Completed)
Plan: Plan 1/1 Complete
Status: Milestone v13.0 Shipped (Completed)
Last activity: 2026-09-09 — Completed Phase 104: Parity Verification, Windows Single-File Build & Milestone Audit.

## Operator Next Steps

- Milestone v13.0 complete and archived. Ready for next milestone initialization.
