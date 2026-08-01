# Phase 51: Multi-Page Raw PDF Ingestion - Context

**Gathered:** 2026-08-01
**Status:** Ready for planning

<domain>
## Phase Boundary

System correctly parses page count of unmanaged `.pdf` drops, updates `state.json` with the correct physical page count, and audits the full page count successfully. Updates `report.json` to properly track these operations.

</domain>

<decisions>
## Implementation Decisions

### Page Count Extraction Strategy
- Use the native `pypdf` library (already present in the project) to accurately count the physical pages of raw PDFs dropped into the folder.
- When an orphan physical `.lnk` is mapped to a raw PDF, set the `end_page` in the `DocumentGroup` so it accurately maps to multiple physical pages if needed (i.e. `start_page + actual_pdf_pages - 1`).

### Reporting & Tracking
- Ensure `report.json` correctly logs the ingested page counts (e.g. `raw_files_processed`, `duplicates_adopted`, etc.).
- Update the metrics so the UI visualizer accurately reflects the true page count added by raw drops.

### Claude's Discretion
None

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pypdf.PdfReader` can be imported to read the lengths of PDFs.
- `src/reconcile/core.py` handles orphan adoption and report logging.

### Established Patterns
- Reconciliation report dict (`report`) is generated in `reconcile/core.py` and returned.

### Integration Points
- `src/reconcile/core.py` orphan adoption logic for `unmatched_lnks` where `new_page` and `new_group` are appended to `state.json`.

</code_context>

<specifics>
## Specific Ideas

- User explicit instruction: "in phase 51, it should also update the report.json (you've kept that in mind right?)."

</specifics>

<deferred>
## Deferred Ideas

None

</deferred>
