# Phase 50: Cross-House Contamination Immunity - Context

**Gathered:** 2026-08-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Identify any shortcut (`.lnk`) that points to a target outside the current house's `.source_files` directory and treat it as a foreign object, filtering it out of the reconciliation pipeline.

</domain>

<decisions>
## Implementation Decisions

### Detection & Handling Strategy
- Check if the absolute target path of the shortcut is inside the current house's `.source_files` directory.
- If it points anywhere else (another house, Desktop, random folder), it is an "external shortcut".
- Do not parse UUIDs or overcomplicate the check.
- Treat external shortcuts as "foreign objects" and simply remove them from the processing pipeline (ignore them just like `.doc` files).
- No complicated quarantining or cross-house UUID tracking.

### Claude's Discretion
None

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/utils/fs.py` handles reading `.lnk` targets via `batch_read_shortcut_targets`.

### Established Patterns
- The system already filters out non-PDF/non-lnk files in `main.py` and `src/reconcile/core.py`.
- We can add the path prefix check during the initial physical shortcut scanning loop in `reconcile/core.py`.

### Integration Points
- `src/reconcile/core.py`: Where physical `.lnk` files are gathered and mapped to `vault_ids`.

</code_context>

<specifics>
## Specific Ideas

- User emphasized: "I feel like we should not care about if a file is from a different house or not. the only thing we need to care about is if this is an external shortcut or not. If it is an external shortcut, we treat it like foreign object and remove it. why add complicated logic."

</specifics>

<deferred>
## Deferred Ideas

None

</deferred>
