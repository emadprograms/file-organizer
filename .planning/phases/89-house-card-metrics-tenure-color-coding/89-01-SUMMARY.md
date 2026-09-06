# Phase 89 Summary: House Card Metrics & Tenure Color-Coding

## Completed Work
- Updated `TreeItemResponse` model in `src/api/models.py` with `current_tenant`, `duration_category`, `subtitle`, `total_documents`, and `category_counts`.
- Updated `/api/tree` in `src/api/routes.py` and `src/presentation/export_static.py` to extract active resident, calculate duration (<5y -> short, 5-10y -> medium, >10y -> long), total document counts, and category breakdown.
- Rendered styled house cards in `index.html` with:
  - Green left border & badge for `< 5 Yrs` (`border-l-emerald-500`, `bg-emerald-50 text-emerald-800`).
  - Yellow left border & badge for `5–10 Yrs` (`border-l-amber-500`, `bg-amber-50 text-amber-800`).
  - Red left border & badge for `> 10 Yrs` (`border-l-rose-500`, `bg-rose-50 text-rose-800`).
  - Tenant name and residency start / duration.
  - Total document count badge and category breakdown pills.

## Verification
- Verified by backend tests in `tests/test_api_grid_overview.py`.
- Verified by Playwright tests in `tests/frontend/test_grid_view.py` (`test_tenure_color_coding`).
