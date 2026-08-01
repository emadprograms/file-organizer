# Phase 55: Shortcut Target Hijack / Corruption - Context

**Gathered:** 2026-08-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Reconciler detects `.lnk` targets that have been modified outside the Vault or broken. Instead of treating the modified shortcut as a user deletion or an external file, the system actively auto-repairs it by relying on `state.json` as the source of truth for where it should point.

</domain>

<decisions>
## Implementation Decisions

### Shortcut Auto-Repair Strategy
- When gathering physical `.lnk` files during reconciliation, compare each `.lnk`'s current target path against the vault ID it *should* have according to the pre-loaded `state.json`.
- If the `.lnk` file is mapped in `state.json` but points to the wrong vault PDF (e.g. was hijacked to another document) or points outside the vault entirely (broken/corrupted), **do not delete it**.
- Instead, invoke the shortcut creation logic to seamlessly rewrite the `.lnk` file's target back to the correct vault PDF corresponding to its `vault_id` in the state.
- Log an auto-repair event in the console so the user knows it fixed a broken link.

### Claude's Discretion
None

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/utils/fs.py` handles creating and reading shortcuts.

### Established Patterns
- Reconciliation treats `state.json` as authoritative for existing mappings.

### Integration Points
- `src/reconcile/core.py` scanning loop.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly clarified: "what would we do if in case the shortcut broke accidentally you know what do we do so we just make sure that I want to discuss 55 more in detail". The agreed approach is auto-repair.

</specifics>

<deferred>
## Deferred Ideas

None

</deferred>
