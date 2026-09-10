---
slug: 260910-navbar-search-upload-divider
title: Add Subtle Vertical Divider and Balanced Spacing Between Search and Circular Plus Button
status: in-progress
created_at: 2026-09-10
---

# Quick Task: Navbar Search and Upload Action Divider

## Objective
Add an elegant vertical divider and balanced breathing room between the search bar (`#btn-search-trigger`) and the circular upload action button (`#btn-ingest-trigger`) in the top navbar.

## Implementation Steps
1. In `src/api/static/index.html`:
   - Add a subtle vertical hairline divider (`<div class="h-5 w-px bg-slate-200/90 mx-0.5 select-none" aria-hidden="true"></div>`) between the search trigger and the circular button.
   - Adjust container spacing to `gap-3.5` with `mx-0.5` on the divider for balanced 16px visual clearance on both sides.
   - Bump script cache buster version tag to `v=260910-9`.
2. Sync static assets to `web-net/wwwroot/` with `dotnet build web-net/FileOrganizer.Web.csproj`.
3. Verify with tests:
   - Vitest: `npm run test:frontend`
   - Playwright: `.venv/bin/pytest tests/frontend/test_ingest_batch_playwright.py tests/frontend/test_delete_doc_dialog_playwright.py -v`
4. Update `SUMMARY.md` and `STATE.md`.
5. Commit and push.
