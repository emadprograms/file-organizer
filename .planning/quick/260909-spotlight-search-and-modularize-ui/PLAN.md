---
slug: 260909-spotlight-search-and-modularize-ui
date: 2026-09-09
description: "Spotlight Command Palette modal with grouped/breadcrumb results and index.html JS modularization"
status: complete
---

# Quick Task: Spotlight Command Palette & UI Modularization

## Objectives
1. **Backend Search Enrichment (`src/api/models.py`, `src/api/routes.py`)**:
   - Enrich `SearchResultResponse` with: `area_id`, `house_id`, `tenant_name`, `category`, `date`, `vault_id`, `is_manual`, `extra_info`.
   - Update `search()` query in `routes.py`:
     - Houses: include area, tenure, document count.
     - Tenants: include house, date range / active status, area.
     - Documents: JOIN tenants to include tenant name, category folder, date, vault_id, and manual lock status.
   - Maintain backwards-compatibility for legacy disk search.

2. **Modularize JavaScript (`src/api/static/`)**:
   - Split monolithic `<script>` in `index.html` into structured modules under `src/api/static/js/`:
     - `spotlight.js`: Spotlight command palette controller, keyboard nav (`↑`, `↓`, `Enter`, `Esc`), grouped rendering (Houses, Tenants, Documents) with full breadcrumbs (`Area › House › Tenant › Folder`), direct document viewer launch.
     - `doc-manager.js`: Document management modal (`...`), folder move/copy, custom `14+` sequential folder creation, manual lock toggle & reset, drag-and-drop.
     - `tenant-manager.js`: House settings & tenant management modal, add/remove rows, present checkbox toggle, save & reallocate.
     - `app.js`: Application state, hash routing, sidebar tree, categories, timeline, grid view, PDF viewer.
   - Clean up `index.html`: Replace raw top-right search input with an elegant search trigger button (`⌘K`).

3. **Verification**:
   - Run backend test suite (`pytest`).
   - Run Playwright E2E tests (`test_v11_e2e_db.py`).
   - Add new E2E test verifying Spotlight modal opening, section grouping, breadcrumb display, keyboard navigation, and direct document selection.
