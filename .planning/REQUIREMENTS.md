# Milestone v5.5: Pipeline Reversibility & Lossless Undo

## Overview
Currently, the Generation Pass at the end of the pipeline slices the original scanned PDF into the Vault and deletes the original file. This prevents users from easily "undoing" a processed house if they want to re-run the pipeline from scratch. Saving a massive `.pdf` duplicate defeats the Vault's storage deduplication.

This milestone leverages the chronological `[Timeline View]` folder. Because the Timeline perfectly preserves the physical page order of the original scan (`001 - ...`, `006 - ...`), the system can perfectly reconstruct the original deleted PDF on demand by stitching the referenced Vault documents back together in numerical order.

## Requirements

### Functional
1. **`undo` CLI Command:** Implement `python src/main.py undo "D:/Areas/.../House_Dir"`.
2. **Lossless PDF Reconstruction:** 
   - Read `_state.json` and extract the `routed_documents` array.
   - Sort the documents strictly by their `start_page` to ensure perfect chronological scan order.
   - Retrieve the corresponding `doc_<vault_id>.pdf` for each document from the Vault.
   - Use `PyMuPDF` (`fitz`) to merge them into a single continuous `568.pdf` in the exact original sequence.
3. **Restoration & Cleanup:**
   - Place the rebuilt `568.pdf` at the root of the target directory.
   - Completely delete the `.source_files/vault/`, `[Timeline View]/`, all tenant folders, and Jasons (`_report.json`, `_state.json`, etc.).
   - Leave the directory in its virgin, pre-processed state.

4. **`_report.json` Paradigm Shift:**
   - The messy, raw AI per-page extraction (currently saved as `_report.json`) must be hidden away. It should be saved directly into `_state.json` (e.g., as `raw_classified_pages`) or as a hidden `.raw_dump.json`.
   - A *brand new* `_report.json` must be generated at the very end of the pipeline.
   - This new `_report.json` must perfectly mirror the `[Timeline View]`. It will be an array of Grouped Documents, structured sequentially by their scan order (matching the `001`, `006` Timeline numbers), containing their finalized dates, assigned folders, and Vault IDs.
   - This applies to both `create` and `append` modes.

5. **Migration Script:**
   - Build a migration script that scans existing processed houses.
   - It will take the old, messy `_report.json` and ingest it into `_state.json`.
   - It will then generate the new, grouped `_report.json` based on the finalized timeline structure to bring old houses up to the v5.5 standard.

6. **Testing:**
   - Update existing tests to reflect the new `_report.json` generation.
   - Add new end-to-end tests for the `undo` command.
   - Add tests for the `migrate` script.
