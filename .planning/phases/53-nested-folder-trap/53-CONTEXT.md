# Phase 53: Nested Folder Trap - Context

**Gathered:** 2026-08-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Reconciler natively supports `.lnk` files in arbitrary nested directories. `target_folder` path is accurately extracted. Verification correctly validates shortcuts in sub-folders without forcing flat schemas.

</domain>

<decisions>
## Implementation Decisions

### Nested Hierarchy Handling
- Maintain the exact, fully relative nested path in `target_folder` (e.g., `Tenant A/Contracts/2023`). Do not flatten it.
- Ensure the reconciler's `glob` or `rglob` correctly traverses all subdirectories recursively.

### Timeline Location Tags
- When generating the timeline `.lnk` filename, use the deepest parent folder name as the location tag to keep it clean (e.g., `[2023]`).

### Claude's Discretion
None

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Path.rglob('*.lnk')` recursively finds shortcuts.
- `lnk.relative_to(target_dir)` automatically handles deeply nested relativity.

### Established Patterns
- The system already extracts `rel_path = lnk.relative_to(target_dir).as_posix()`.
- We just need to ensure `target_folder` uses `Path(rel_path).parent.as_posix()`, which handles arbitrary depths out-of-the-box. We just need a concrete verification test to lock it in.

### Integration Points
- `src/reconcile/core.py` and `tests/test_reconcile_*.py`.

</code_context>

<specifics>
## Specific Ideas

- The user absolutely loves this approach: "what you can do is then you can manage your own folders in your own way later however you like it I actually really like this approach I I like this approach yeah just save the shortcut in whatever folder the user has created... Just a quick question how will it be affected in the timeline I guess it'll just be based on how recently it was added right".

</specifics>

<deferred>
## Deferred Ideas

None

</deferred>
