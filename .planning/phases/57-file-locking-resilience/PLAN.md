# Phase 57: File Locking Resilience - Plan

**Status:** Ready for execution

## Objective
Implement a strict Preflight Lock Detection check at the very beginning of the reconciliation pipeline to prevent any partial execution or state mutation when files are locked by another process (e.g., opened by a user over the network).

## Plan Steps

1. **Implement Preflight Lock Detection**
   - **File:** `src/reconcile/core.py` (and potentially a utility file if more appropriate)
   - **Action:** At the absolute start of the reconciliation process, before any state is mutated or files are moved, scan the target directories to collect all relevant files (e.g., Vault PDFs, `.lnk` shortcuts, and `.json` state files).
   - **Details:**
     - Create a robust detection mechanism that safely tests each discovered file for write locks (e.g., attempting an exclusive `open()` in append mode or using `os.access`).
     - Ensure this check does not modify file contents or metadata if the file is unlocked.

2. **Enforce Immediate Abort on Lock Detection**
   - **File:** `src/reconcile/core.py`
   - **Action:** Handle any lock detection by immediately aborting the reconciliation run.
   - **Details:**
     - If a `PermissionError` or equivalent lock indicator is encountered for *any* file, immediately halt execution.
     - Print a clear, actionable error message to the console specifying the locked file. Example: `"ABORTED: The following file is currently locked by another process or user: {filepath}. Please ask the user to close it and try again."`
     - Terminate the process (e.g., `sys.exit(1)`) to guarantee zero side-effects. Do not proceed with any partial state modifications, ghost adoptions, or metadata updates.

3. **Add Tests for Lock Resilience**
   - **File:** `tests/test_reconcile_phase57.py`
   - **Action:** Create integration tests that verify the preflight check.
   - **Details:**
     - Setup a test house and artificially lock a vault PDF or state file (e.g., by keeping an open file handle to it).
     - Run the reconciler.
     - Verify that the reconciler exits early with the correct error code and message.
     - Verify that absolutely no state or files were modified in the process.

## Verification
- Run the newly created integration tests to ensure that a simulated file lock results in a clean, immediate abort without any state mutation.
