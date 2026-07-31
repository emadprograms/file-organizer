# Phase 35: Migration Script

## Objective
Build a one-click migration script to upgrade older v4 direct-placement houses to the new v5 vault+shortcut architecture.

## Requirements
- **MIGRATE-01**: Migration script converts existing houses from direct-placement to vault format
- **MIGRATE-02**: Migration preserves current folder structure as user-pinned locations
- **MIGRATE-03**: Migration includes dry-run mode to preview changes without modifying files

## Success Criteria
- Dry-run script lists changes without modifying files
- Migration converts existing structured folders to vault format and pins locations in `_3_routed_and_finalized.json` with `user_locked: true`
- Rebuilds `00_Timeline_View/`
- Copies the physical PDFs into `.source_files/vault/doc_{uuid}.pdf`
- Replaces the physical PDFs with `.lnk` shortcuts
- Tests pass.
