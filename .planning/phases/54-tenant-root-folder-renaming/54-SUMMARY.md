# Phase 54: Tenant Root Folder Renaming - Summary

## Decisions
- **Snap-back Enforcement:** Enforced strict snap-back of any shortcuts moved to non-canonical top-level folders. `user_locked` is only permitted if the shortcut is moved within a valid canonical tenant directory.
- **Aggressive but Safe Cleanup:** Implemented `shutil.rmtree` for any root folder that is not recognized as a canonical folder, `.source_files`, or `[Timeline View]`, PROVIDED it does not contain unmanaged physical files (like unprocessed PDFs).

## Lessons
- **Implicit Test Dependencies:** Found that earlier tests (`test_reconcile_bidirectional.py`) assumed users could freely create custom top-level folders. The new stricter rules required updating those tests to align with the authoritative `tenants.yaml` requirement.
- **Patch Bypassing:** Accidentally bypassed a mock patch by locally importing `FileOrganizer` inside a function, causing the real implementation to execute and breaking test assertions. Removed the local import to respect global patches in testing.

## Patterns
- **Safety Checks:** We continually see the pattern of "verify if the folder contains unmanaged files before deleting" as a safeguard against data loss.

## Surprises
- Found that raw PDF ingestion tests (Phase 43) also placed files in non-canonical top-level folders, which collided with the strict Phase 54 cleanup. Updated Phase 43 tests to drop PDFs in canonical subfolders instead.
