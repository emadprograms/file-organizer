# Phase 34: Prepend Mode

## Objective
Rename all references from "append mode" to "prepend mode" across the CLI commands, codebase, and documentation.

## Requirements
- **PREPEND-01**: Rename "append" to "prepend" across all CLI commands, code, and documentation
- **PREPEND-02**: Logic updates so new documents are prepended to `00_Timeline_View/`
- **PREPEND-03**: Remove any legacy "raw append" file generation since we are fully shortcut-based

## Success Criteria
- The CLI command is now `file-organizer watcher --prepend` (if it was `--append`).
- Documentation reflects the new terminology.
- Tests pass.
