# Phase 51 Summary

## Decisions
- Integrated `pypdf` directly in `src/reconcile/core.py` to count pages of physical PDFs during ingestion.
- Re-used the indexing logic from earlier phases to map out `num_pages` virtual entries for both raw PDFs and ghost shortcuts.
- Wrapped `pypdf.PdfReader` in a `try/except` block falling back to 1 page if the PDF is unreadable, maintaining system robustness when dealing with corrupted files or empty files used in tests.

## Lessons & Patterns
- When creating abstractions over physical files (like PageData and DocumentGroup), the initial assumption of "1 file = 1 page" was challenged when raw multi-page PDFs were ingested directly. Extending the loop to `num_pages` provides a seamless fix.
- Proper fallback mechanisms (like `try/except`) are important when invoking external libraries on unpredictable user files.

## Surprises
- Found that `pypdf.PdfReader` aggressively validates PDFs on initialization, causing existing test suites (which frequently touched empty dummy `.pdf` files) to fail with `EmptyFileError`. Catching this exception and defaulting to `num_pages = 1` was necessary to unbreak the CI test suite.
