# Phase 52: Corrupted Vault File Safeguards - Context

**Gathered:** 2026-08-01
**Status:** Ready for planning

<domain>
## Phase Boundary

0-byte or corrupt vault files do not crash the reconciler. Timeline view handles corrupt vault links safely. Verification flags corrupt vault documents.

</domain>

<decisions>
## Implementation Decisions

### Vault Error Handling
- Use a `try...except` block or simple file size check when attempting to read the page count of a vault file (e.g., using `pypdf.PdfReader`).
- If a `PdfReadError` or `ValueError` (or EOFError) occurs because the vault file is 0-bytes or fundamentally corrupt, catch the exception and log a high-visibility warning.
- DO NOT crash the reconciler or delete the corrupted vault file. Keep its metadata intact in `state.json`.

### Timeline Tagging
- If a document is detected as corrupt during the timeline generation (or if it was flagged during state load), dynamically append `[CORRUPT]` to its `.lnk` filename in the timeline.

### Claude's Discretion
None

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pypdf` exceptions can be used to catch corrupt reads.

### Established Patterns
- Graceful degradation — similar to how we handle external shortcuts.

### Integration Points
- `src/reconcile/core.py` where we verify vault file page counts (from Phase 51 or generally).
- `src/reports/timeline.py` or wherever timeline linking occurs.

</code_context>

<specifics>
## Specific Ideas

- The user has approved the `[CORRUPT]` tagging and explicit non-deletion.

</specifics>

<deferred>
## Deferred Ideas

None

</deferred>
