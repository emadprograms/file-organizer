# Phase 93-01 Summary: Legacy Data Migration & Storage Restructuring

## Overview
Phase 93 (Plan 93-01) implements the complete migration engine and CLI for Milestone v11.0. It migrates legacy house repositories (v5-v10 formats containing `.source_files/`, `state.json`, `report.json`, `1_tenants.yaml`, `.lnk` shortcuts, and Arabic category subdirectories) into the v11 relational SQLite database backend and clean two-folder on-disk structure (`{area}/{house_id}/batches/` and `{area}/{house_id}/vault/`).

---

## Key Achievements

### 1. Test-Driven Development (`tests/test_migration_v11.py`)
Developed a comprehensive 10-test suite covering:
- **`test_extract_house_id`**: Robust house ID extraction across Arabic names, prefixes, and plain IDs.
- **`test_normalize_date`**: Universal date parsing for ISO `YYYY-MM-DD`, `YYYY/MM/DD`, `DD-MM-YYYY`, partial year-months, and null markers (`NONE`, `present`).
- **`test_migrate_house_success`**: Full end-to-end migration validating database records (`areas`, `houses`, `tenants`, `batches`, `pages`, `documents`) and on-disk file reorganization.
- **`test_migrate_house_idempotency`**: Verifies that re-running migration on an already migrated house completes with zero errors and produces zero duplicate rows.
- **`test_migrate_house_dry_run`**: Verifies that `dry_run=True` leaves disk structure and database untouched.
- **`test_migrate_house_fallback_tenants_and_placeholder_batch`**: Handles houses lacking `tenants.yaml` or raw scans by inferring tenants from metadata and creating valid placeholder batches.
- **`test_migrate_house_no_rename_flag`**: Validates `--no-rename` preserves legacy house folder naming while restructuring internal files.
- **`test_migrate_areas_batch`**: Verifies batch migration across entire area hierarchies with area code mapping.
- **`test_migration_integrity_verification`**: Deep integrity audit verifying disk-to-DB alignment and detecting missing or empty vault files.
- **`test_cli_migrate_v11`**: End-to-end CLI integration test using `sys.argv` and `main()`.

### 2. Migration Engine (`src/migration/v11_migration.py`)
- **Metadata Ingestion**: Parses legacy `state.json` (`cleaned_pages`, `fine_categorized_pages`, `grouped_documents`, `routed_documents`, `manifest`) and `report.json`.
- **Tenant Extraction**: Prioritizes `1_tenants.yaml`, falls back to report/state tenant fields, and finally extracts from folder name or fallback default.
- **Batch Processing**: Discovers raw source PDF scans in `.source_files/` or house root, renames/moves to `{house_id}/batches/batch_1_{name}.pdf`, records page count via PyMuPDF (`fitz`), and handles placeholder batches if missing.
- **Vault Migration**: Moves all `doc_{vault_id}.pdf` files into `{house_id}/vault/`, populating `documents` and linking `pages.vault_id`.
- **Relational Integrity**: Enforces strict SQLite foreign keys (`areas` -> `houses` -> `tenants` & `batches` -> `documents` -> `pages`).
- **Disk Cleanup**: Safely removes obsolete `.lnk` shortcuts, Arabic category folders, `[Timeline View]`, and `.source_files/` directory upon successful migration.
- **Folder Renaming**: Renames house directory to clean house number (e.g. `514 - محمد مبارك` -> `514`) unless disabled.

### 3. CLI Integration (`src/main.py`)
Added the `migrate-v11` subcommand to `src/main.py`:
```bash
python src/main.py migrate-v11 [--areas-root PATH] [--target-dir PATH] [--db-path PATH] [--dry-run] [--no-rename] [--verbose]
```
- Defaults to `config.areas_root_path` and `config.area_mappings`.
- Supports single-house targeting via `--target-dir`.
- Preview mode supported via `--dry-run`.
- Folder rename suppression supported via `--no-rename`.

---

## Verification Results
- `python3 -m pytest tests/test_migration_v11.py tests/db/ tests/test_core_config_parsing.py`
- **31 passed in 0.32s** with 100% success rate across all migration and database tests.
