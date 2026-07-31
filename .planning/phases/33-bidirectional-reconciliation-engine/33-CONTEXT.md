# Phase 33: Bidirectional Reconciliation Engine

## Objective
Implement bidirectional reconciliation engine to diff old vs new `.source_files/` and manage `.lnk` files.

## Success Criteria
- Re-running `file-organizer` over an existing house correctly diffs old vs new `.source_files/`.
- Updates old vault `.lnk` files if paths changed or deletes if removed.
- Rebuilds `.lnk` files correctly.
- Avoids orphaned shortcut links.
