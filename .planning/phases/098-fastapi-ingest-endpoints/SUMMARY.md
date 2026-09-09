# Phase 98 Summary: FastAPI Ingest Endpoints (POST /api/ingest & POST /api/ingest/preview-ai)

## Overview
Phase 98 implements high-performance, robust FastAPI endpoints for unified document ingestion in Milestone v12.0. It exposes `POST /api/ingest` supporting `manual` (instant, zero-AI), `assisted` (AI-suggested metadata auto-fill + manual ingestion), and `auto_split` (multi-document batch splitting via `v11_ingest`) modes, as well as `POST /api/ingest/preview-ai` for single-document preview analysis without writing to the database or file vault.

---

## Key Achievements

### 1. Ingestion Pydantic Models (`src/api/models.py`)
- **`IngestResponse`**: Represents unified ingestion output containing `status`, `mode`, `vault_id`, `vault_ids`, `batch_id`, `page_count`, `documents_created`, `house_id`, `area_id`, and `message`.
- **`AIPreviewResponse`**: Represents non-destructive preview analysis containing `status`, `page_count`, `suggested_title`, `suggested_category`, `suggested_date`, `suggested_tenant_name`, `suggested_house_id`, and `suggested_area_id`.

### 2. Multi-Mode Ingestion Endpoint (`POST /api/ingest` in `src/api/routes.py`)
- **Multipart Form Upload**: Accepts `file` (`UploadFile`), `mode` (`manual`, `assisted`, `auto_split`), `area_id`, `house_id`, and optional metadata fields (`tenant_id`, `tenant_name`, `category`, `arabic_title`, `primary_date`, `notes`, `dry_run`).
- **File Validation**: Enforces `.pdf` file extension and verifies `%PDF` binary header magic bytes.
- **Tenant Auto-Resolution & Creation**:
  - If `tenant_name` is provided without `tenant_id`, matches against existing house tenants (case-insensitive) or dynamically registers a new tenant in the house.
  - If neither `tenant_id` nor `tenant_name` is supplied, automatically resolves to the house's active tenant or dynamically creates `Default Tenant`.
  - Validates that explicitly passed `tenant_id` exists and belongs to the specified house.
- **Mode Execution**:
  - `manual`: Uses `ingest_document_manual`, defaults category to `"13-رسائل متنوعة"` and title to the uploaded filename if not specified.
  - `assisted`: Automatically extracts preview metadata if title, category, date, or tenant are omitted, auto-populates them, and persists through manual ingestion.
  - `auto_split`: Delegates multi-page document splitting to `ingest_pdf_to_house` (`v11_ingest`), returning `vault_ids` and `documents_created`.
- **Cache Invalidation**: Triggers `clear_tree_cache()` on completion so the dashboard UI updates immediately.

### 3. Non-Destructive Preview Endpoint (`POST /api/ingest/preview-ai` in `src/api/routes.py`)
- **Zero-DB Guarantee**: Analyzes documents strictly in memory/read-only mode with zero mutations to SQLite tables or the disk vault.
- **Heuristic Engine & Robust Text Extraction**:
  - Extracts text from initial pages using PyMuPDF `fitz`.
  - Applies Unicode NFKC normalization and handles visual-order/reversed Arabic text seamlessly.
  - Detects date patterns across ISO (`YYYY-MM-DD`), standard European (`DD-MM-YYYY`), and Arabic month names (`يناير` - `ديسمبر`), converting Arabic-Indic digits to Latin digits.
  - Classifies documents across standard categories (`05-عقود`, `06-كهرباء وماء`, `03-أمر تخصيص`, `10-صيانة`, etc.) using bilingual keyword matching.
  - Infers titles from subjects, tenant names from keywords or house registry, and house IDs from text hints.
  - Works 100% offline with zero token costs, with optional LLM client enhancement if configured on the application state.

### 4. Comprehensive Test Suite (`tests/test_ingest_api.py`)
11 integration tests covering all requirements:
- `test_post_ingest_manual_mode`: Multipart upload, database document/pages verification with `is_manual=1`, batch and vault files created.
- `test_post_ingest_manual_inline_tenant_creation`: Verifies dynamic tenant creation when `tenant_name` is provided.
- `test_post_ingest_manual_default_tenant_creation`: Verifies fallback to `Default Tenant` for houses without tenants.
- `test_post_ingest_invalid_file_extension`: Validates 400 error on non-PDF file upload.
- `test_post_ingest_invalid_file_signature`: Validates 400 error on non-%PDF content.
- `test_post_ingest_invalid_mode`: Validates 400 error on unsupported ingestion modes.
- `test_post_ingest_tenant_mismatch`: Validates 400 error when tenant belongs to another house.
- `test_preview_ai_suggestions_and_no_db_writes`: Verifies AI preview suggestions and ensures zero DB rows or files are written.
- `test_preview_ai_invalid_file`: Validates 400 error on preview for invalid file format.
- `test_post_ingest_assisted_mode`: Verifies metadata auto-population for omitted fields in assisted mode.
- `test_post_ingest_auto_split_mode`: Verifies batch splitting execution in auto_split mode.

---

## Verification Results

```bash
.venv/bin/pytest tests/test_ingest_api.py tests/test_ingest_manual.py tests/test_api_v11.py -v
======================== 31 passed, 6 warnings in 0.95s ========================
```

Requirements **API-04** and **API-05** are fully satisfied.
