# Phase 41: State & YAML Integrity Rules

## Objective
The verifier cross-references `state.json` against actual folder layout. Orphan PDFs in the vault are detected. Ghost legacy JSONs and physical PDFs outside the vault are flagged. Tenant structures match `tenants.yaml`.

## Scope
- Build set-difference logic between physical files (vault and shortcuts) and logical state (`state.json`).
- Ensure untracked shortcuts are surfaced as WARNING instead of ERROR.
- Detect orphaned `.pdf` files inside `vault/`.

## Implementation Steps
1. Implement `state.json` parser inside verification engine.
2. Compare manifest lists against vault lists (Orphans).
3. Compare manifest logical locations against physical shortcut locations (Misplaced/Missing shortcuts).
4. Update log levels for untracked shortcuts.

## Status
- **Status:** COMPLETED
- **Completed On:** 2026-08-01
