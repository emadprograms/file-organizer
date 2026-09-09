# Phase 97 Summary: Ingest Engine Core (Manual Ingest Pipeline & Page Inheritance)

## Overview
Phase 97 implements the zero-AI manual document ingestion pipeline (`src/ingest/manual_ingest.py`) for Milestone v12.0. It enables instant, deterministic ingestion of documents directly into the SQLite database and the clean disk hierarchy (`{area}/{house}/batches/` and `{area}/{house}/vault/`) without any LLM API calls, preserving full relational page inheritance in the `pages` table.

---

## Key Achievements

### 1. Zero-AI Manual Ingestion Pipeline (`src/ingest/manual_ingest.py`)
- **Direct PDF Processing**: Uses PyMuPDF (`fitz`) for rapid page counting and local text extraction (`extract_pdf_text`) with zero network latency and zero LLM dependencies.
- **Batch Registration**: Inserts batch record with `status='completed'`, `page_count=N`, and stores original scan in `{house}/batches/batch_{batch_id}_{filename}`.
- **Vault Slicing**: Slices or copies PDF directly into `{house}/vault/doc_{vault_id}.pdf` using a secure UUID hex identifier.
- **Relational Document Record**: Records document row in `documents` with `is_manual=1`, page count, primary date, Arabic title, category, and optional user notes.
- **Dry-Run Preview**: Supports `dry_run=True` to compute page count and return preview metadata without writing to database or filesystem.
- **Atomic Rollback**: Database operations run within `get_db()` transaction; newly created files on disk are automatically cleaned up if an exception occurs.

### 2. Relational Page Inheritance (`ING-04`)
- Populates `pages` table for every page `1..N`:
  - `tenant_id`, `resolved_date`, `category`, and `fine_category` inherited from the document.
  - `vault_id` foreign key correctly links each page to the parent document.
  - `page_number = 1..N`.
  - `is_continuation = (page_number > 1)` (first page is `False`, subsequent pages are `True`).
  - `content_explanation = f"Page {page_number} of {arabic_title}"`.
  - `subject = arabic_title if page_number == 1 else None`.
  - `fine_category_reason = "Manually verified by user"`.
  - LLM scratchpad fields (`expected_tenant_name`, `expected_house_number`, `raw_date`, `sender`, `receiver`) strictly remain `NULL`.

### 3. Repository Enhancements (`src/db/repository.py`)
- **Document Notes Support**: Updated `add_document` and `Repository.add_document` to accept and persist `notes`.
- **Document Search Helper**: Added `search_documents(conn, query, house_id=None)` and `Repository.search_documents(query, house_id=None)` searching across title, category, notes, and vault ID.
- **Page Retrieval by Vault**: Added `get_pages_by_vault_id(conn, vault_id)` and `Repository.get_pages_by_vault_id(vault_id)`.

### 4. Comprehensive Test Suite (`tests/test_ingest_manual.py`)
10 tests covering all functional and error requirements:
- `test_single_page_manual_ingest`: Single-page document ingestion, batch/vault files, document metadata, page fields.
- `test_multi_page_manual_ingest_page_inheritance`: Multi-page document with continuation flags, inherited tenant/category/date, and NULL scratchpad fields.
- `test_dry_run_mode`: Previews metadata without touching filesystem or database.
- `test_error_missing_pdf`: Raises `FileNotFoundError` for non-existent files.
- `test_error_zero_pages_pdf`: Raises `ValueError` for 0-page or empty PDF files.
- `test_error_invalid_tenant`: Raises `ValueError` for non-existent tenants or tenants belonging to a different house.
- `test_search_retrievability`: Verifies search by title, notes, partial vault ID, category filter, and page retrieval.
- `test_vault_slicing_mode`: Validates optional page range slicing (`start_page`..`end_page`) into vault.
- `test_extract_pdf_text`: Validates local text extraction without AI.
- `test_atomic_rollback_on_failure`: Verifies cleanup of disk artifacts when a database error occurs.

---

## Verification Results

```bash
.venv/bin/pytest tests/test_ingest_manual.py
======================== 10 passed in 0.81s ========================

.venv/bin/pytest tests/db/ tests/test_api_v11.py tests/test_ingest_v11.py tests/test_ingest_manual.py
======================= 40 passed, 6 warnings in 26.85s ========================
```
100% test pass rate across core and new test suites.
