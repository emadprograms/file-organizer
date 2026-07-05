# Phase 4: Output Structure & Reconciliation - Context

**Gathered:** 2026-07-05
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase takes the split `DocumentGroup` objects produced by Phase 3 and writes them into the final structured directory hierarchy: `output/{house_id}/{tenant_name} {year_start}-{year_end}/{topic_folder}/{filename}.pdf`. It also adds checkpoint/resume for Pass 2, page count reconciliation, and a JSON manifest mapping every input page to its output file.

</domain>

<decisions>
## Implementation Decisions

### Folder Structure & Naming

- **D-01:** Topic folder names use a number prefix + English slug, matching the existing `routing.py` pattern (e.g., `01_requests_and_applications`, `02_personal_details`, ..., `13_others`). The 13 folder names are already defined in `src/processing/routing.py` -> `FOLDER_ROUTING`.
- **D-02:** Tenant directory names use the canonical Arabic name + timeline year range: e.g., `علي محمد 2018-2023/`. The existing `sanitize_filename()` (FS-01) handles Windows-reserved char stripping and NFC normalization -- no transliteration needed.
- **D-03:** The Unassigned folder's period is inferred from the **date range of unassigned pages** (min_date to max_date of pages routed to Unassigned). Folder name: `غير محدد {year_start}-{year_end}/` (or just `غير محدد/` if all dates are null).
- **D-04 (user override):** Topic subdirectories are created **on-demand only** -- a folder is created when at least one document routes to it. Empty topic folders are NOT pre-created, even though OUT-03 stated "even if empty". This was explicitly overridden by the user during discussion.

### Checkpoint / Resume

- **D-05:** Two checkpoint files are used:
  1. `output/{house_id}_cleaned.json` -- Pass 1 checkpoint (already implemented in `organize.py`). No changes needed.
  2. `output/checkpoints/grouped.json` -- Pass 2 checkpoint: the full `DocumentGroup` list serialized as JSON, saved **after LLM grouping/routing completes and before PDF splitting begins**. On restart, if this file exists, skip grouping/routing and go straight to PDF splitting.
- **D-06:** Both checkpoint files are deleted **after a successful reconciliation pass** (page counts match). This is the cleanup trigger -- not on pipeline completion alone.

### Reconciliation Manifest & Report

- **D-07:** Manifest format: JSON file at `output/{house_id}_manifest.json`. Structure:
  ```json
  {
    "summary": {
      "house_id": "...",
      "total_input_pages": N,
      "total_output_pages": N,
      "output_file_count": N,
      "unaccounted_pages": []
    },
    "per_page": [
      {
        "page_index": 0,
        "tenant": "...",
        "date": "...",
        "output_file": "relative/path/to/file.pdf",
        "page_in_output": 1
      }
    ]
  }
  ```
- **D-08:** If the reconciliation check fails (total input pages != total output pages), the pipeline **halts and raises a `RuntimeError`**. Mismatches must not silently pass. The manifest is still written before raising so the operator can inspect which pages are unaccounted for.

### FileOrganizer Refactor

- **D-09:** `src/processing/organizer.py` is **rewritten in-place** -- same filename and same `FileOrganizer` class name (so `organize.py`'s import is unchanged), but rebuilt with the full Phase 4 responsibility:
  1. Accept the `house_id` as a parameter to set the house-level root dir
  2. Build tenant dirs with canonical Arabic name + timeline
  3. Handle the Unassigned tenant folder with inferred period
  4. Create topic dirs on-demand only (D-04)
  5. Write PDFs using `extract_pdf_segment()` from `split.py`
  6. Return a page-index -> output-file mapping for use in reconciliation
- **D-10 (agent discretion):** Reconciliation logic lives in a separate helper function `run_reconciliation(summary, total_input_pages, house_id, output_dir)` -- called from `organize.py` after `FileOrganizer.organize()` returns. This keeps `FileOrganizer` focused on writing files and reconciliation as an explicit final step.

### Agent Discretion
- Manifest is written to `output/{house_id}_manifest.json` (alongside the cleaned.json checkpoint) -- consistent location with other pipeline artifacts.
- The `output/checkpoints/` dir is created by `organize.py` before the grouping step runs, so checkpoint writes never fail due to missing parent.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` -- OUT-01 through OUT-06, LOG-04, DIFF-02, DIFF-03 (the Phase 4 requirements). D-04 user override: OUT-03 is intentionally not fully implemented (empty folders not pre-created).

### Project Context
- `.planning/PROJECT.md` -- Key decisions section (hardcoded routing rules, two-pass architecture, Arabic filename format)

### Existing Code -- Must Read Before Implementing
- `src/processing/organizer.py` -- Current `FileOrganizer` to be rewritten; understand existing logic before replacing
- `src/processing/routing.py` -- `FOLDER_ROUTING` dict defines the 13 folder names and their allowed categories; this is the source of truth for topic folder names
- `src/processing/split.py` -- `extract_pdf_segment()` is the PDF splitting primitive; reuse, do not reimplement
- `src/core/schemas.py` -- `DocumentGroup` Pydantic model (fields: `start_page`, `end_page`, `primary_tenant`, `category`, `dates`, `reason`, `brief_arabic_title`, `folder_path`, `is_direct_routed`)
- `src/core/utils.py` -- `sanitize_filename()` for Arabic name safety on Windows; `normalize_date()` for date string formatting
- `src/organize.py` -- Entry point wiring Pass 1 -> Pass 2 -> FileOrganizer; Phase 4 adds checkpoint load/save calls and reconciliation call here

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/processing/split.py` -> `extract_pdf_segment(source_pdf, start_page, end_page, output_path)` -- PyMuPDF-based PDF segment extraction; already tested and used in Phase 3
- `src/processing/routing.py` -> `FOLDER_ROUTING` dict -- the authoritative list of 13 topic folder names (keys) and their allowed source categories (values); Phase 4 uses the keys to name dirs
- `src/core/utils.py` -> `sanitize_filename()`, `normalize_date()` -- used for all filesystem writes
- `src/core/schemas.py` -> `DocumentGroup` -- already has `folder_path`, `primary_tenant`, `dates`, `start_page`, `end_page`; Phase 4 consumes these directly

### Established Patterns
- Pass 1 checkpoint pattern (in `organize.py` lines 92-107): check file existence -> skip or run -> write JSON. Replicate this pattern for the Pass 2 grouped checkpoint.
- All file writes use atomic temp-rename via FS-04 pattern (already in `fs_utils.py`) -- apply to manifest and checkpoint writes.
- `defaultdict(set)` used in current `FileOrganizer` for de-duplication of filenames per dir -- keep this pattern.

### Integration Points
- `organize.py` `main()` is the integration point: after `pipeline._group_and_route_documents()`, add checkpoint save; after `organizer.organize()`, add reconciliation call.
- `FileOrganizer.organize()` signature stays compatible: `(documents, source_pdf, output_base_dir, config)` -- config is currently `None` and can stay that way since routing is hardcoded.
- The `house_id` is already available in `organize.py`'s `main()` scope -- pass it to `FileOrganizer.organize()` or use it to construct `output_base_dir` before the call.

</code_context>

<specifics>
## Specific Ideas

- Tenant dir format: `{canonical_arabic_name} {year_start}-{year_end}/` (space separator between name and years, hyphen between years)
- Unassigned dir format: `غير محدد {year_start}-{year_end}/` (or `غير محدد/` when no dates available)
- Checkpoint file: `output/checkpoints/grouped.json` -- serialized as `[group.model_dump() for group in documents]`; deserialized as `[DocumentGroup(**d) for d in data]`
- Manifest written at: `output/{house_id}_manifest.json`
- Checkpoints deleted after: reconciliation passes (counts match)

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 4-Output Structure & Reconciliation*
*Context gathered: 2026-07-05*
