---
wave: 3
depends_on:
  - 01-exceptions-and-sys-exit-PLAN.md
  - 03-pymupdf-compression-PLAN.md
files_modified:
  - src/processing/grouping.py
  - src/processing/organizer.py
  - src/processing/routing.py
  - src/processing/split.py
  - src/processing/pipeline.py
  - src/organize.py
autonomous: true
---

# Plan: Sub-packages Refactoring

## Requirements
- REF-02
- REF-03

## Context
Break bloated files in `src/processing/` into sub-packages and split oversized functions across the application into smaller, single-responsibility functions.

## Tasks

<task>
<read_first>
- src/processing/routing.py
- src/processing/pipeline.py
</read_first>
<action>
Create `src/processing/routing/` directory.
Move `FOLDER_ROUTING` and `CATEGORY_TO_FOLDERS` definitions to `src/processing/routing/config.py`.
Move `route_document` and `RoutingResponse` to `src/processing/routing/router.py`. When doing so, ensure that circular dependencies between `src.processing.routing.router` and `src.core.schemas` (or `src.llm.llm`) are avoided (e.g., by using forward references, local imports, or migrating shared schema models appropriately).
Create `src/processing/routing/__init__.py` exposing `route_document`.
Delete `src/processing/routing.py`. Update imports in `src/processing/pipeline.py`.
</action>
<acceptance_criteria>
- `src/processing/routing.py` is removed.
- `src/processing/routing/__init__.py` exports `route_document`.
- Pipeline imports are updated successfully.
- No circular dependency errors occur when importing `src.processing.routing.router` or `src.core.schemas`.
</acceptance_criteria>
</task>

<task>
<read_first>
- src/processing/grouping.py
- src/processing/pipeline.py
</read_first>
<action>
Create `src/processing/grouping/` directory.
Move `category_presplit`, `verify_groups`, and `merge_chunks` to `src/processing/grouping/utils.py`.
Move `process_with_shrink` to `src/processing/grouping/core.py`.
Split the oversized `process_with_shrink` function by extracting the inner chunk processing logic into a separate `_process_chunk` helper function.
Create `src/processing/grouping/__init__.py` exposing `process_with_shrink`.
Delete `src/processing/grouping.py`. Update imports.
</action>
<acceptance_criteria>
- `src/processing/grouping.py` is removed.
- `process_with_shrink` is broken down into smaller helper functions (less than 50 lines).
- `src/processing/pipeline.py` imports work correctly.
</acceptance_criteria>
</task>

<task>
<read_first>
- src/processing/organizer.py
- src/organize.py
</read_first>
<action>
Create `src/processing/organizer/` directory.
Move `run_reconciliation` to `src/processing/organizer/reconciliation.py`.
Move `FileOrganizer` to `src/processing/organizer/core.py`.
Split the oversized `FileOrganizer.organize` method (150 lines) into smaller methods:
1. `compute_tenant_folders`
2. `ensure_target_directories`
3. `process_documents`
Create `src/processing/organizer/__init__.py` exposing `FileOrganizer` and `run_reconciliation`.
Delete `src/processing/organizer.py`. Update imports in `src/organize.py`.
</action>
<acceptance_criteria>
- `src/processing/organizer.py` is removed.
- `FileOrganizer.organize` calls smaller helper methods instead of doing all work in one monolithic block.
- `src/organize.py` imports work correctly.
</acceptance_criteria>
</task>

<task>
<read_first>
- src/processing/split.py
- src/processing/organizer/core.py
</read_first>
<action>
Create `src/processing/pdf/` directory.
Move `extract_pdf_segment` to `src/processing/pdf/extract.py`.
Move `compress_pdf` to `src/processing/pdf/compress.py`.
Create `src/processing/pdf/__init__.py` exposing `extract_pdf_segment` and `compress_pdf`.
Delete `src/processing/split.py`. Update imports in `src/processing/organizer/core.py`.
</action>
<acceptance_criteria>
- `src/processing/split.py` is removed.
- `extract_pdf_segment` is imported from `src.processing.pdf`.
</acceptance_criteria>
</task>

## Artifacts this phase produces
- `src/processing/routing/__init__.py`
- `src/processing/routing/config.py`
- `src/processing/routing/router.py`
- `src/processing/grouping/__init__.py`
- `src/processing/grouping/core.py`
- `src/processing/grouping/utils.py`
- `src/processing/organizer/__init__.py`
- `src/processing/organizer/core.py`
- `src/processing/organizer/reconciliation.py`
- `src/processing/pdf/__init__.py`
- `src/processing/pdf/extract.py`
- `src/processing/pdf/compress.py`
- `FileOrganizer.compute_tenant_folders` method
- `FileOrganizer.ensure_target_directories` method
- `FileOrganizer.process_documents` method
- `_process_chunk` function in `src/processing/grouping/core.py`

## Must Haves
### truths
- D-01: Break bloated files in `src/processing/` into sub-packages for better isolation.
- The `src/processing/` directory contains no flat logic files (except maybe `pipeline.py`).
- The `organize` and `process_with_shrink` functions are split into smaller functions, none exceeding 50 lines.

### prohibitions
- Bloated monolithic files inside `src/processing/` are not permitted.
