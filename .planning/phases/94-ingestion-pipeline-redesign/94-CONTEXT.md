# Phase 94: Ingestion Pipeline Redesign — Context

## Goal
Redesign the file ingestion engine to write directly into the SQLite database (`batches`, `pages`, `documents`) and the clean two-folder disk structure (`batches/` and `vault/`). Eliminate all index-shifting math on new uploads ("prepend"), delete the legacy reconciler loop, and remove .lnk shortcut generation.

## Scope
- Implement a database-backed ingestion workflow (`src/ingest/v11_ingest.py` or refactored `src/ingest/core.py`).
- Register raw multi-page upload as a `batches` record and save physical file in `{area}/{house}/batches/`.
- Insert page-level OCR/extractions into `pages` with `(batch_id, page_number)`.
- Match/resolve tenants against `tenants` table.
- Group pages into documents, slice PDFs into `{area}/{house}/vault/doc_{vault_id}.pdf`.
- Insert into `documents` table and link `pages.vault_id`.
- Complete elimination of:
  - `run_reconciliation` and `FileOrganizer.organize` (no .lnk shortcuts).
  - Page index shifting loops (`doc['start_page'] += shift_amount`).
  - `state.json` and `report.json` writing.
- Strict TDD in `tests/test_ingest_v11.py` with mock LLM calls.
