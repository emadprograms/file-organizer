# Phase 49: 1-to-Many Shortcut Mapping - Context

**Gathered:** 2026-08-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Update `state.json` to handle 1 vault ID to multiple shortcuts. Ensure physical page counts remain accurate regardless of shortcut count, and Timeline View generates without duplicating pages.

</domain>

<decisions>
## Implementation Decisions

### Data Model Migration (state.json schema)
- Change `"shortcut_name"` string to `"shortcuts"` list of strings — natively supports 1-to-many.
- Auto-migrate on next read — convert the old string to a list containing that single string.
- Yes, use a Set internally — prevents duplicates if reconciliation runs twice or shortcuts overlap.
- Remove from manifest, treat as orphaned — just like the current system does for 1-to-1 deletions.

### Timeline View Generation
- Display it once — using the "primary" or "first discovered" shortcut path as its location tag.
- Add a subtle indicator — like "(+ 1 other location)" to the location tag.
- Use the vault file's standard metadata/creation date — sorting remains unaffected by the number of shortcuts.
- Use the underlying vault filename — this serves as the canonical name in the timeline to avoid conflicts.

### Claude's Discretion
None

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- None specifically for this refactor, but we will utilize existing timeline builder and state management loops.

### Established Patterns
- Auto-migration during `state.json` loads has been done in earlier phases.
- `src/reconcile/core.py` handles the reconciliation loop and state tracking.
- `src/reports/timeline.py` handles timeline generation.

### Integration Points
- `src/reconcile/core.py` state loading and saving.
- `src/reports/timeline.py` data ingestion from `state.json`.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
