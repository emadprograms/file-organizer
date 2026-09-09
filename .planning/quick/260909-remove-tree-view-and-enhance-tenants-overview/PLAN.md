---
slug: 260909-remove-tree-view-and-enhance-tenants-overview
date: 2026-09-09
description: "Remove tree view entirely, make houses overview default, and show short overview of tenants on house cards"
status: complete
---

# Quick Task: Remove Tree View & Enhance House Cards Tenants Overview

## Objectives
1. **Remove Tree View Entirely (`src/api/static/index.html`, `src/api/static/js/app.js`)**:
   - Eliminate tree view rendering (`createTreeNodes`), tree chevrons, tree item drag handlers, and tree CSS.
   - Remove `#view-mode-tree` and `#view-mode-grid` segmented buttons; make the Houses/Areas overview the default view of the application.
   - Retain `#view-mode-db` (Database Inspector) as a dedicated button/link.
   - Sidebar displays the clean list of Areas with house counts.
   - Selecting an area displays its houses overview immediately.
   - Back button (`#back-to-grid-btn`) updated to read `← Back to Houses` instead of `Back to Grid`.
   - Update URL hash handling so navigating to `/` or `#/area/{area}` loads the area overview directly without requiring `/grid/` prefixes (while maintaining backward compatibility with `/grid/area/` deep links).

2. **House Cards Short Tenants Overview**:
   - Instead of displaying category document counts (`category_counts: [cat: count]`) on the overview cards:
   - Display a meaningful **Tenants Overview** (`سجل المستأجرين / Tenants Overview`):
     - Total count of tenants for that house.
     - Active/current tenant with status indicator (`🟢`) and tenure dates.
     - Previous tenants with status indicator (`⚪`) and occupancy periods.
     - Clean, compact visual layout with badges and occupancy timeline.
   - Maintain tenure color coding (Green <5y, Yellow 5-10y, Red >10y) and total documents count badge.

3. **Intuitive Back to Tenants Navigation**:
   - Provide intuitive, clean navigation to go back to the tenant list (Tenancy Register) when viewing a tenant's folders/documents.
   - Replace awkward in-title Arabic button with:
     1. A dedicated top navbar button `#back-to-tenants-btn` (`← Back to Tenants`) placed logically alongside `#back-to-grid-btn` (`← {area} Houses`).
     2. A sleek tenant header banner inside `#document-list` with `[← Back to Tenants]` button and tenant name badge.
     3. Clean breadcrumb title `${houseId} / ${tenantName}` without awkward embedded buttons.

4. **Testing & Verification**:
   - Update existing test suites that referenced `#view-mode-tree` or `#view-mode-grid` (`tests/frontend/test_grid_view.py`, `tests/frontend/test_navigation.py`, `tests/frontend/test_v11_e2e_db.py`, `tests/frontend/test_tabs.py`, `tests/frontend/test_pdf_preview.py`, `tests/frontend/test_backend_safra_d.py`, `tests/frontend/test_safra_c_missing_arrows.py`).
   - Create new test file `tests/frontend/test_tenants_overview_grid.py` verifying:
     - Short tenants overview on house cards.
     - Removal of tree view.
     - Default houses overview.
     - Intuitive navigation from house -> tenant -> back to tenants list -> back to houses overview.
   - Run all backend and frontend Playwright tests to ensure 100% pass rate.
   - Commit and push to `origin main`.
