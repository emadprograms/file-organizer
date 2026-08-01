# Phase 51: Multi-Page Raw PDF Ingestion - Plan

## 1. Import `pypdf` in `src/reconcile/core.py`
- Import `PdfReader` from `pypdf` at the top of `src/reconcile/core.py` to allow reading the page counts of physical PDFs. (The library is already present in the project's virtual environment).

## 2. Update Ghost Adoption to Support Multi-Page (Phase 33/43 logic)
- In the loop for adopting ghost shortcuts (`for vault_id, lnks in physical_lnk_by_vault.items():` where `vault_id not in vault_id_to_pages:`):
  - Before creating the `PageData` and `DocumentGroup`, instantiate `reader = pypdf.PdfReader(str(vault_pdf))`.
  - Calculate `num_pages = len(reader.pages)`.
  - Wrap the `PageData` and `routed_data["per_page"]` generation in a loop `for i in range(num_pages):`.
  - Set `original_index = start_page_idx + i` for each `PageData` and `page_index = start_page_idx + i` for each routed data entry.
  - Set the `content_explanation` to include `(Page {i+1}/{num_pages})`.
  - Create exactly one `DocumentGroup` covering the span: `start_page=start_page_idx`, `end_page=start_page_idx + num_pages - 1`.

## 3. Update Raw PDF Ingestion to Support Multi-Page (Phase 43 logic)
- In the loop for ingesting raw PDFs (`for pdf_path in physical_pdf_files:`):
  - After moving the PDF to the vault (or immediately if dry run), read it: `reader = pypdf.PdfReader(str(dest_vault_pdf))`.
  - Calculate `num_pages = len(reader.pages)`.
  - Similar to ghost adoption, wrap the `PageData` and `routed_data["per_page"]` creation in a `for i in range(num_pages):` loop.
  - Map indices from `start_page_idx` to `start_page_idx + num_pages - 1`.
  - Create a single `DocumentGroup` spanning this range.

## 4. Update Report Logging for Page Counts
- Add `raw_pdf_pages_ingested` and `ghost_pages_adopted` to the initial `report` dictionary in `src/reconcile/core.py` (around line 65).
- Increment these counters by `num_pages` when adopting ghosts or ingesting raw PDFs.
- Update the `logger.info("=== RECONCILIATION SUMMARY ===")` block to print these new page-based metrics alongside the file-based ones.

## 5. Verification Integrity
- `src/core/verification.py` already checks that `len(cleaned_pages) == len(manifest)`. Since we're pushing `num_pages` elements into both `pages` and `routed_data["per_page"]`, this invariant will hold naturally. No changes are required to the verifier, but we should run it to ensure the page count mismatch error does not trigger.

## 6. Testing
- If there is a reconciliation test suite (e.g. `tests/test_reconcile.py`), ensure that raw PDF ingestion with a multi-page PDF correctly splits into multiple `PageData` records.
