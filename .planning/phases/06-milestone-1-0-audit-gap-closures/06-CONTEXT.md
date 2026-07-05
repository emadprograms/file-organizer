# Phase 6: Milestone 1.0 Audit Gap Closures - Context

**Gathered:** 2026-07-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Resolve integration gaps found in the v1.0 Milestone Audit to ensure full pipeline correctness across phase boundaries, focusing on specific fixes across Pass 1 cleaning, Pass 2 grouping/routing, and Output structure logic.

</domain>

<decisions>
## Implementation Decisions

### Unassigned Naming
- **D-01:** Translate the 'Unassigned' folder to 'غير مخصص (فترة مستنتجة)' to match the Arabic output structure. If there are no dates available, use 'غير مخصص'.

### Reconciliation Report Formatting
- **D-02:** Print the detailed reconciliation breakdown as a formatted Rich table. If the reconciliation check fails, print the table first before raising the RuntimeError to help debugging.

### Direct-routed Filenames
- **D-03:** For direct-routed documents that span multiple pages, just use the first page's date for the filename (e.g. 2020-01-01.pdf).

### the agent's Discretion
None

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Specifically the Phase 6 requirements (CLN-02, CLN-04, CLN-08, OUT-05, OUT-03, FS-04, LOG-04, GRP-04, GRP-12, LLM-08)
- `.planning/REQUIREMENTS.md` — To understand the original requirements for the gap closures
- `.planning/STATE.md` — To understand the current state of the project

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/processing/organizer.py`: Existing `FileOrganizer` and reconciliation structure (needs formatting updates).
- `src/processing/routing.py`: Needs update for `Unassigned` folder name to Arabic.
- `src/core/fs_utils.py`: Contains atomic temp-rename pattern `atomic_write`, to be used for checkpoints and fallbacks.

### Established Patterns
- Checkpoints currently use standard file writes. Need to switch to `fs_utils.atomic_write` or similar.

### Integration Points
- `organize.py` entry point prints the final reconciliation output.
- `pipeline.py` anchor category checking needs alignment with JSON.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-Milestone 1.0 Audit Gap Closures*
*Context gathered: 2026-07-05*
