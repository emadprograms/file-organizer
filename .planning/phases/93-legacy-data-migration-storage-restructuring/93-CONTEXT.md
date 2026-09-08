# Phase 93: Legacy Data Migration & Storage Restructuring — Context

## Goal
Migrate legacy house directories (v5-v10 formats with state.json, report.json, .lnk shortcuts, and Arabic subdirectories) into the v11 SQLite database architecture and simplified two-folder on-disk structure (`batches/` and `vault/`).

## Scope
- Implement `src/migration/v11_migration.py` with idempotent migration logic.
- Parse `state.json` / `report.json` to populate `areas`, `houses`, `tenants`, `batches`, `pages`, and `documents` tables.
- Restructure house files: move/preserve vault PDFs into `vault/`, master raw scans into `batches/`.
- Safe cleanup of legacy `.lnk` shortcuts, Arabic category folders, and redundant JSON state files.
- Support safe dry-run mode and detailed migration audit reporting.
- 100% test coverage in `tests/test_migration_v11.py` covering legacy mock data, idempotency, and data preservation.
