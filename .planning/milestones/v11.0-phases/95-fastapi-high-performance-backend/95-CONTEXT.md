# Phase 95: FastAPI High-Performance Backend — Context

## Goal
Overhaul the FastAPI backend (`src/api/routes.py`, `src/api/server.py`) to query SQLite directly for tree structure, grid overview, timeline, categories, and search. Eliminate SMB globbing overhead, retire complex filesystem caching workarounds, and deliver sub-10ms API response times.

## Scope
- Update `src/api/routes.py` to route requests through SQLite when a database is available (`app.state.db_path` or `config.db_path`), with fallback to legacy filesystem mode if DB is absent.
- Implement SQL-backed endpoints:
  - `GET /api/tree`: Single/dual indexed SQL queries returning the full area/house/tenant/counts tree in < 10ms.
  - `GET /api/areas/{area_id}/houses/{house_id}/timeline`: SQL query with `ORDER BY primary_date DESC`.
  - `GET /api/areas/{area_id}/houses/{house_id}/categories`: SQL query grouped by category.
  - `GET /api/search`: Fast SQL LIKE / indexed search across houses, tenants, and documents.
  - `GET /api/areas/{area_id}/houses/{house_id}/pdf/{vault_id}`: Serves `{house_dir}/vault/doc_{vault_id}.pdf`.
- Update `src/core/config.py` to include `db_path` configuration setting.
- Strict TDD in `tests/test_api_v11.py` and regression verification with `tests/test_api_grid_overview.py`.
