# Phase 96: E2E Verification & UI Parity — Context

## Goal
Verify end-to-end functionality of the complete database-backed system (SQLite backend + clean storage architecture + FastAPI + web UI) via Playwright tests and full backend test suite, ensuring 100% feature parity, zero regressions, and lightning-fast responsiveness.

## Scope
- Create `tests/frontend/test_v11_e2e_db.py` running real Playwright browser sessions against the SQLite-backed FastAPI server.
- Verify all UI features against SQLite:
  - Tree View expansion & hierarchy
  - Grid View toggle & area selection
  - House Card metrics & tenure color-coding (<5y, 5-10y, >10y)
  - Drill-down navigation into Categories & Timeline tabs
  - Fast SQL search & navigation
  - PDF serving from `{house}/vault/`
- Run the full test suite across the entire project.
- Document results and finalize Milestone v11.0.
