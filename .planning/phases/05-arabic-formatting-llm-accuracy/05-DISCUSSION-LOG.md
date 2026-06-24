# Phase 5 Discussion Log

- **Area:** 'Al-' Prefix Handling
  - **Presented:** Regex vs completely disabled
  - **Selected:** Disable stripping entirely — Rely strictly on exact matches and let the AI output normalized names.

- **Area:** Zero-Padded Folder Format
  - **Presented:** Dots vs underscores vs dashes
  - **Selected:** "01_CategoryName" (e.g. `01_عقود السكن`)

- **Area:** Dynamic Folder Generation
  - **Presented:** Write-time vs initialization-time
  - **Selected:** Just-in-time (Write-time) — Only create the folder right before a PDF is actually saved into it.

- **Area:** Retry Limits & Fallback
  - **Presented:** Move to UNKNOWN vs halt pipeline
  - **Selected:** Move the document to an UNKNOWN fallback folder, log the failure, and continue processing.
