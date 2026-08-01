# Phase 54: Tenant Root Folder Renaming - Context

**Gathered:** 2026-08-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Reconciler enforces consistency when a user arbitrarily renames a top-level tenant folder. Instead of passively tracking the new name, the system actively auto-corrects the folder name back to the canonical tenant name defined in `tenants.yaml`, acting as a safety net.

</domain>

<decisions>
## Implementation Decisions

### Folder Name Auto-Correction Strategy
- During the initial discovery phase of reconciliation, before scanning `.lnk` files, compare the existing physical directory name of the tenant against the `tenant_name` expected by `tenants.yaml` for this house/tenant.
- If the physical directory name differs (e.g. user renamed it to "Tenant A (Archived)"), immediately rename the physical directory back to the canonical name using `os.rename` or `Path.rename`.
- This ensures all `target_folder` paths remain consistent with the YAML source of truth and prevents state divergence or endless tracking loops.
- Log an auto-correct event in the console so the user knows why the folder was renamed back.

### Claude's Discretion
None

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `os.rename` or `shutil.move` for safely renaming the directory.

### Established Patterns
- Reconciliation treats `tenants.yaml` as authoritative.

### Integration Points
- `src/reconcile/core.py` (during tenant setup/initialization before deep scanning).

</code_context>

<specifics>
## Specific Ideas

- The user explicitly requested this active enforcement: "whenever the reconciliation runs it renames it to the current tenant name no matter anyone changes it to anything it changes itself to the correct tenant name and make sure that the shortcuts are pointing to the correct folder".

</specifics>

<deferred>
## Deferred Ideas

None

</deferred>
