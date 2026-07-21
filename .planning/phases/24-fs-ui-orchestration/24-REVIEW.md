---
phase: 24-fs-ui-orchestration
status: warning
files_reviewed: 8
critical: 0
warning: 2
info: 3
total: 5
---

# Code Review: Phase 24

## Summary
The implementation of the File-System UI Orchestrator and the PID-based lock utility meets the requirements of the phase. The lock recovery mechanism using `os.kill` is correctly implemented. The orchestrator's state machine successfully handles the `_Proposed.pdf` and ` OK.pdf` transitions. 

However, there are a few issues identified: a TOCTOU race condition in the lock utility, a minor memory leak in the orchestrator's file size tracking, and some missing edge-case handling for error files and path traversal.

## Findings

### WR-01: TOCTOU race condition in PID lock acquisition
- **Severity**: Warning
- **File**: `src/fs_ui/lock.py`
- **Description**: The lock acquisition mechanism checks if the lockfile exists, reads the PID, checks liveness, and then overwrites the lockfile with its own PID. This sequence is not atomic. Two processes starting simultaneously could both see a stale lockfile, both verify the old PID is dead, and both write their own PID to the file. Both would then proceed under the assumption they hold the exclusive lock, leading to duplicate orchestrators and subsequent `FileNotFoundError`s during file renaming.
- **Recommendation**: For true atomicity, consider using `fcntl.flock` or `os.open` with `O_CREAT | O_EXCL` flags combined with a retry loop.

### WR-02: Unbounded growth of `file_sizes` dictionary (Memory Leak)
- **Severity**: Warning
- **File**: `src/fs_ui/orchestrator.py`
- **Description**: `FSUIOrchestrator.file_sizes` tracks the size of seen files across iterations. When a file is processed (renamed to `_Proposed.pdf` or finalized), its original path string remains in the dictionary forever. Over a long-running process with many files, this dictionary will grow indefinitely.
- **Recommendation**: Periodically prune `self.file_sizes` by removing keys that are no longer present in the `inbox_dir`, or rebuild the dictionary entirely during each polling iteration.

### IN-01: Duplicate exception raising code in `acquire_lock`
- **Severity**: Info
- **File**: `src/fs_ui/lock.py`
- **Description**: The `PermissionError` and `else` blocks in the `os.kill` `try...except` block contain identical logic: `raise LockExistsError(f"Lock held by active PID: {pid}")`.
- **Recommendation**: Consolidate these branches to reduce code duplication.

### IN-02: Missing collision handling for `_Failed.pdf` and `_Error_Invalid_Format.pdf`
- **Severity**: Info
- **File**: `src/fs_ui/orchestrator.py`
- **Description**: The `finalize` method correctly handles collisions by appending an incrementing counter `(1)`. However, the `propose` method uses `os.rename` unconditionally when appending `_Failed.pdf` or `_Error_Invalid_Format.pdf`. On POSIX systems, this will overwrite any existing error files with the same name.
- **Recommendation**: Implement collision avoidance (like the counter used in `finalize`) for error files as well.

### IN-03: Potential Path Traversal in `finalize` parsing
- **Severity**: Info
- **File**: `src/fs_ui/orchestrator.py`
- **Description**: `finalize` extracts `area_id` and `house_id` directly from `clean_name.split(" ", 2)`. While `is_relative_to(areas_root)` prevents escaping the `areas_root` entirely, if a user specifically names a file `Area .. Tenant Date Type OK.pdf`, `house_id` resolves to `..`. This would cause the file to be processed into `areas_root/.source_files` rather than a specific house folder.
- **Recommendation**: Validate that `area_id` and `house_id` do not contain `.` or `/` characters after parsing.
