---
phase: 35-migration-script
plan: 35
subsystem: core
tags: [python, v5]

requires: []
provides:
  - milestone feature completed

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified: []

key-decisions:
  - "None"

patterns-established:
  - "None"

requirements-completed:
  - MIGRATE-01
  - MIGRATE-02
  - MIGRATE-03

coverage: []
duration: 10m
completed: 2026-08-01
status: complete
---

# Phase 35: Migration Script - Summary

## Objective
Build a one-click migration script to upgrade older v4 direct-placement houses to the new v5 vault+shortcut architecture without data loss.

## Work Completed
- **MIGRATE-01**: Created `src/migration/v5_migration.py` which scans the house folder for PDFs and dynamically moves them to `.source_files/vault/doc_{uuid}.pdf`.
- **MIGRATE-02**: Configured the script to generate `.lnk` shortcuts in the exact original paths of the PDFs, retaining the original categorization. Updated `_3_routed_and_finalized.json` to assign `vault_id` and mark existing placements as `user_locked: true` so reconciliation preserves them.
- **MIGRATE-03**: Implemented `--dry-run` logic in `migrate_to_v5` to trace actions without touching physical files.
- Added a `migrate` subcommand to the CLI `src/main.py`.
- Automated test coverage in `tests/test_migration.py`.

## Verification
- Dry-run successfully previews the migration plan.
- Live migration successfully converts standard PDFs to `.lnk` files pointing to the hidden vault.
- `00_Timeline_View/` is rebuilt correctly containing the new `.lnk` files.
- Test suite passes.

## Next Steps
This wraps up the milestone! We will now proceed with autonomous completion steps.
