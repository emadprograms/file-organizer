---
phase: "24"
plan: "04"
subsystem: "fs-ui-orchestrator"
tags: ["fs-ui", "propose", "finalize"]
requirements-completed: []
key-files.modified: ["src/fs_ui/orchestrator.py"]
key-decisions:
  - "Moved full pipeline processing (cleaning, grouping, routing) into propose() to ensure accuracy."
  - "Modified propose() to extract independent PDFs for each routed document, correctly populating all 6 fields, and creating isolated sidecar JSON states."
  - "Added SHA256 hashing in propose() to store a pdf_hash.txt in .tmp_{stem} directories, enabling finalize() to confidently map user-renamed OK.pdf files back to their state directory."
  - "Refactored finalize() to be fully programmatic, merging state JSONs and invoking run_generation_pass to construct final PDFs without redundant LLM calls."
---

# Phase 24 Plan 04: Fix propose/finalize behavior Summary

Refactored `FSUIOrchestrator` to execute the complete extraction and pipeline routing within the `propose()` step. This allows the system to present the user with fully resolved filenames in the Inbox. `finalize()` now operates deterministically, tracking approved files via SHA256 hashes even if renamed, updating final state JSONs, and applying file movements programmatically.

## Accomplishments

- Refactored `propose()` to execute `process_unclassified_pdf`, `_clean_documents`, `_group_documents`, and `_route_documents`.
- Changed `propose()` to split multi-document PDFs into individual `_Proposed.pdf` files, each with an accurately populated 6-field filename based on its document group.
- Implemented isolated sidecar JSON state tracking in `.tmp_*` directories, linking files via `pdf_hash.txt` to resist filename alterations by the user.
- Adapted `finalize()` to detect approved documents via hash, apply any user-driven filename edits back into the JSON state, and programmatically merge state and invoke `run_generation_pass`.
- Updated `process_inbox()` cleanup logic to handle new proposed filenames securely.

## Deviations from Plan

None - plan executed exactly as written, with robust hash-based rename tracking.

## Self-Check: PASSED
