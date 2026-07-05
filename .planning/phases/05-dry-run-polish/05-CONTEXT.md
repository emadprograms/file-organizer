# Phase 5: Dry Run & Polish - Context

**Gathered:** 2026-07-05
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase implements a `--dry-run` flag to preview the pipeline output (folder structure, file names, routing decisions) without writing physical files or PDFs, and adds any final polish to the File Organizer Post-Processor.

</domain>

<decisions>
## Implementation Decisions

### Output Format
- **D-01:** Both a tree-like folder view and a tabular summary should be presented in the terminal during a dry run to provide comprehensive visibility into the planned folder structure and routing.

### Checkpoint Interaction
- **D-02:** Dry run mode should read from existing checkpoints (e.g., `cleaned.json`, `grouped.json`) to save time and API costs if they exist, but it MUST NOT write new checkpoints or the reconciliation manifest to disk, keeping the state clean.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — Requirement DIFF-01 (Dry run / preview mode).

### Project Context
- `.planning/PROJECT.md` — Core value and constraints.

### Existing Code -- Must Read Before Implementing
- `src/organize.py` — Entry point where the `--dry-run` flag will be parsed and passed down.
- `src/processing/organizer.py` — Where file writes and PDF extractions happen; these need to be bypassed in dry-run mode.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/organize.py` argument parser can easily be extended with `--dry-run`.
- Existing `logger` instances can be used to output the tabular summary and tree view.

### Established Patterns
- Checkpoint checking logic is already present in `organize.py`. The dry-run logic can piggyback on this but skip the write steps.
- File operations in `organizer.py` (like `os.makedirs` and `extract_pdf_segment`) need conditional execution based on a `dry_run` boolean passed in the config or explicitly.

### Integration Points
- `src/organize.py` `main()`: Pass the `dry_run` flag to `FileOrganizer`.
- `FileOrganizer.organize()`: Return the same results but skip `extract_pdf_segment` and `os.makedirs` when `dry_run=True`. Output the dry-run specific logs at the end of the script or inside `organizer.py`.

</code_context>

<specifics>
## Specific Ideas

- The dry run should effectively process everything (or load from checkpoints) and print what *would* happen.
- Avoid writing `output/{house_id}_manifest.json` during a dry run.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-Dry Run & Polish*
*Context gathered: 2026-07-05*
