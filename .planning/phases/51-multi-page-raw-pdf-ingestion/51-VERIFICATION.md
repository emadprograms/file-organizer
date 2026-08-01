# Phase 51 Verification

- **Code Implemented**: Modified `src/reconcile/core.py` to extract actual page counts via `pypdf` for both raw PDF ingestion and ghost shortcut adoption.
- **Tests Created**: Added `tests/test_reconcile_phase51.py` covering multi-page raw PDF ingestion and multi-page ghost shortcut adoption.
- **Test Results**: All tests, including the existing and new phase 51 tests, pass successfully.
- **Robustness**: Added `try/except` around `pypdf.PdfReader` to gracefully fallback to 1 page if the file cannot be read (e.g. empty or corrupted mock files).
