# Phase 58: Lossless Undo Command

## Objective
Implement a lossless `undo` command that reconstructs the original categorized PDF from the vault files using `_state.json` and PyMuPDF, and then wipes the directory clean of all generated folders.

## Steps
1. Add `undo` command parser to `src/main.py`.
2. Implement `run_undo(target_dir: Path)` in `src/pipeline/undo.py`.
   - Extract `house_id` from `target_dir`.
   - Read `.source_files/{house_id}_state.json`.
   - Extract `routed_documents` and sort them by `start_page`.
   - Stitch `doc_{vault_id}.pdf` files into a single `{house_id}.pdf` at the root of `target_dir` using PyMuPDF (`fitz`).
   - Remove `.source_files/`, `[Timeline View]`, and all tenant folders (i.e. delete all contents in `target_dir` except `{house_id}.pdf`).
3. Add a test suite `tests/pipeline/test_undo.py` to thoroughly verify this command.
4. Update `ROADMAP.md` and `STATE.md`.
