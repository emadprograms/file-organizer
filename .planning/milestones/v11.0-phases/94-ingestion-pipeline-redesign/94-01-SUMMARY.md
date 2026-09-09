# Phase 94-01 Summary: Ingestion Pipeline Redesign

## Overview
Phase 94 (Plan 94-01) implements the complete v11 database-backed ingestion workflow (`src/ingest/v11_ingest.py`) for Milestone v11.0. It allows ingesting multi-page scanned PDFs directly into the SQLite database and the clean two-folder disk structure (`{area}/{house_id}/batches/` and `{area}/{house_id}/vault/`), completely replacing legacy index-shifting math, .lnk shortcut generation, state.json/report.json tracking, and the legacy reconciler loop.

---

## Key Achievements

### 1. Test-Driven Development (`tests/test_ingest_v11.py`)
Developed a comprehensive test suite covering:
- **`test_single_batch_ingest`**: Full end-to-end ingestion of a 3-page PDF:
  - Verifies `batches` record created with `status='completed'`, `page_count=3`, and filename `batch_1_{name}.pdf`.
  - Verifies `pages` records created with OCR extractions, normalized dates, tenant mapping, and fine categories.
  - Verifies sliced vault PDFs created in `{house}/vault/doc_{vault_id}.pdf` with exact page counts (2 pages and 1 page).
  - Verifies `documents` records created with correct `vault_id`, `house_id`, `tenant_id`, `batch_id`, `primary_date`, `arabic_title`, `category`, and `page_count`.
  - Verifies `pages.vault_id` foreign keys properly populated.
  - Verifies zero `.lnk` shortcuts, zero `state.json`/`report.json`, and zero legacy directories created.
- **`test_multi_batch_prepend_preserves_older_records`**:
  - Ingests a second 2-page PDF into the same house.
  - Verifies new batch row (`batch_id=2`) and new page rows (`page_number` in `[1, 2]`).
  - **Zero Index Shifting**: Verifies batch 1 records, page numbers, and documents are 100% untouched.
  - Verifies `list_documents_by_house` orders all 4 documents chronologically across batches by `primary_date DESC`.
- **`test_dry_run_ingest`**: Verifies that `dry_run=True` previews ingestion without writing files or database records.
- **`test_rollback_on_error`**: Injects an OCR failure midway through ingestion, verifying complete database transaction rollback (0 batches, 0 pages, 0 documents) and cleanup of disk files (0 orphaned PDFs).
- **`test_cli_parser_v11_options`**: Validates parser handling for `--v11`, `--house-id`, `--area-id`, `--db-path`, `--areas-root`, and `--dry-run`.
- **`test_run_v11_ingest_mode_and_cli`**: Verifies `run_v11_ingest_mode` execution and CLI `main()` dispatch with `--v11`.

### 2. Ingestion Engine (`src/ingest/v11_ingest.py`)
- **Direct Database Integration**: Uses `src.db.connection.get_db` and `src.db.repository.Repository` for atomic, type-safe transactions.
- **Master Scan Batch Registration**: Records uploaded PDFs into `batches` and places them into `{house_id}/batches/batch_{batch_id}_{name}.pdf`.
- **Page Extraction & Classification**: Extracts per-page OCR fields (`category`, `content_explanation`, `expected_tenant_name`, `expected_house_number`, `raw_date`, `sender`, `receiver`, `subject`, `is_continuation`).
- **Tenant Matching & Date Resolution**: Matches against `tenants` table by name, creates new tenant records on demand, normalizes dates to ISO `YYYY-MM-DD`, and fills missing dates via nearest-neighbor proximity matching.
- **Fine Categorization**: Assigns fine categories and reasons per page using `DIRECT_ROUTING_MAP` and `FOLDER_PREFIXES` or LLM categorization.
- **Logical Document Grouping & PyMuPDF Slicing**: Groups pages into document blocks using continuation flags and tenant boundaries, generates unique UUID `vault_id`s, slices physical PDFs into `{house_id}/vault/doc_{vault_id}.pdf`, and updates `pages.vault_id` foreign keys.
- **Failure Resilience**: Atomic rollback deletes partial disk files and rolls back SQLite transactions upon errors.

### 3. CLI Integration (`src/main.py`)
Extended the `ingest` subcommand with `--v11`:
```bash
python -m src.main ingest <input_path> --v11 [--house-id ID] [--area-id ID] [--db-path PATH] [--areas-root PATH] [--dry-run] [--verbose]
```
- Dispatches to `run_v11_ingest_mode`.
- Automatically determines target house and area IDs from directory or file structure if not explicitly provided.
- Full backward compatibility retained for legacy pipeline mode.

---

## Verification Results
Ran test suite:
```bash
./.venv/bin/pytest tests/test_ingest_v11.py tests/test_migration_v11.py tests/db/
```
**30 passed, 5 warnings in 31.11s** (100% pass rate).
