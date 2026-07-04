---
wave: 5
depends_on:
  - 03-PLAN.md
  - 04-PLAN.md
files_modified:
  - src/processing/pipeline.py
  - src/processing/organizer.py
autonomous: true
---

# Phase 3 - Plan 5: Pipeline Integration & Organizer Updates

## Requirements
- GRP-11: Split PDF using PyMuPDF page ranges
- GRP-12: Name output PDFs (title or date only)
- GRP-13: Dateless docs use inferred date

## Review Feedback Incorporation
- **Bypassing Strategy Pattern (Antigravity - MEDIUM)**: *REJECTED.* According to `STATE.md`, the decision was made to drop YAML config and hardcode routing ("Dropped YAML config — simpler, suits the structure"). Re-implementing a strategy pattern here contradicts the explicit project decision to simplify and hardcode the flow. The pipeline will invoke the new hardcoded steps directly.
- **Single-Match Filename State Gap (Antigravity - MEDIUM)**: Organizer logic now explicitly checks `group.is_direct_routed` to decide between `YYYY-MM-DD.pdf` and `YYYY-MM-DD - title.pdf`.

## Tasks

```xml
<task>
  <action>Update `FileOrganizer` naming and splitting logic</action>
  <read_first>
    - src/processing/organizer.py
  </read_first>
  <acceptance_criteria>
    - `FileOrganizer` removes the old declarative grouping/routing logic if present.
    - Uses `group.folder_path` for the destination folder.
    - If `group.is_direct_routed` is True, filename is `YYYY-MM-DD.pdf` (using `group.dates[0]`).
    - If `group.is_direct_routed` is False, filename is `YYYY-MM-DD - {group.brief_arabic_title}.pdf`.
    - If `group.dates` is empty or null, uses `"nodate"` as the date string.
    - Calls `extract_pdf_segment` using `group.start_page` and `group.end_page`.
  </acceptance_criteria>
</task>

<task>
  <action>Wire Phase 3 logic into `pipeline.py`</action>
  <read_first>
    - src/processing/pipeline.py
  </read_first>
  <acceptance_criteria>
    - Replaces old grouping logic in `Pipeline.run()`.
    - Passes `raw_pages` through `category_presplit`.
    - Iterates over category runs, calling `process_with_shrink` on each.
    - Iterates over generated groups, calling `route_document`, and sets `group.folder_path` and `group.is_direct_routed`.
    - Passes the final list of `DocumentGroup` objects to `FileOrganizer`.
  </acceptance_criteria>
</task>
```

## Verification
- Running `python src/organize.py` on a sample creates overlapping chunks, merges them, and splits PDFs into the correct folder layout with correct filenames.

## Must Haves
- Filename formatting strictly branches on `is_direct_routed`.
- Pipeline fully delegates to `process_with_shrink` and `route_document`.

## Artifacts this phase produces
- Modified `FileOrganizer` class
- Modified `Pipeline.run()` execution flow
