# Phase 85 Context

## Requirements
- Backend: Implement `/api/search` endpoint (FastAPI) to search for tenant names and house numbers. The data comes from `.source_files/*_state.json` or `*_report.json`.
- Frontend: Implement Top Navbar with Search Input in Vanilla JS.
  - Handle `Enter` to submit search.
  - Handle `Esc` to clear input and close search results.
  - Display "No results" when there are no matches.
- Technologies: Vanilla JS/DOM, FastAPI, Pytest, Playwright.

## Current State
- The backend has `src/api/routes.py` with `list_houses`, `list_vault_files`, `get_tree`, etc. We need to add `GET /api/search`.
- Frontend is located at `src/api/static`.
- Tests are likely in `tests/api` and `tests/frontend`.

## Strategy
1. Update `src/api/models.py` with `SearchResultResponse` if needed, or directly return a list of results.
2. Update `src/api/routes.py` to add `@router.get("/api/search")`.
3. Update `src/api/static/index.html` (or whatever the main frontend file is) to include a top navbar and search input.
4. Update `src/api/static/app.js` (or similar) to handle keyboard events and DOM updates.
5. Write and verify tests using Pytest and Playwright.
