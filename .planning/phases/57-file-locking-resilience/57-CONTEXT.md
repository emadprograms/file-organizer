# Phase 57: File Locking Resilience - Context

**Gathered:** 2026-08-01
**Status:** Ready for planning

<domain>
## Phase Boundary

System implements a strict pre-flight lock detection check before running any reconciliation logic. If any file (vault PDF or state file) is locked by another process (e.g., opened by a user over the network), the system immediately fails and safely shuts down without modifying any state.

</domain>

<decisions>
## Implementation Decisions

### Pre-Flight Lock Detection
- Before executing any file movements, parsing, or state generation, the reconciler must run a pre-flight pass on all `.lnk` files, vault PDFs, and `.json` state files involved in the operation.
- Use Python's standard `os.access` or attempt an exclusive `open(file, 'a+')` to test for write locks (especially on network drives).
- If a `PermissionError` or lock is detected on *any* file, immediately print a clear error to the console (e.g., "ABORTED: The following file is currently locked by another user: X.pdf. Please ask the user to close it and try again.")
- Halt execution with `sys.exit(1)`. DO NOT proceed with partial reconciliation.

### Claude's Discretion
- Determine the most robust and cross-platform (Windows) way to detect locked files without actually modifying them during the pre-flight check.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- None specifically for lock checking yet, but Python's `open()` handles lock detection naturally on Windows SMB shares.

### Established Patterns
- We already have an early-exit pattern for missing tenant YAMLs or missing directories. We will add this lock check to the very beginning of the reconciliation pipeline.

### Integration Points
- `src/reconcile/core.py` (entry point before state manipulation begins).

</code_context>

<specifics>
## Specific Ideas

- The user wants the absolute safest approach: "we do a preflight log detection and then just we stop if any file is locked we just say that this file is logged by so and so... and then I feel like just free flight log detection and then immediately shut down is the best implementation and the safest one in my opinion".

</specifics>

<deferred>
## Deferred Ideas

None

</deferred>
