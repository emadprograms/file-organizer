# Requirements: v5.0 Vault Architecture & Bidirectional Reconciliation

**Defined:** 2026-07-31
**Core Value:** Documents are safely stored once in an immutable vault; all organization is done via lightweight shortcuts that can be freely rearranged by the user without risk of data loss.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Vault Storage

- [ ] **VAULT-01**: System creates a hidden `.source_files/vault/` directory per house
- [ ] **VAULT-02**: Each document group receives a unique UUID
- [ ] **VAULT-03**: Physical PDFs are stored in vault named by UUID (e.g., `doc_A1B2.pdf`)
- [ ] **VAULT-04**: Vault uses two-phase commit (`.tmp` → rename) to prevent orphans on crash
- [ ] **VAULT-05**: Once a PDF enters the vault it is never moved or renamed

### Windows Shortcuts

- [ ] **LNK-01**: System generates Windows `.lnk` shortcut files using `pylnk3` (pure Python, cross-platform testable)
- [ ] **LNK-02**: Shortcuts placed in categorized Arabic folders (e.g., `10_صيانة/`)
- [ ] **LNK-03**: Shortcuts named with date and document title for readability
- [ ] **LNK-04**: Shortcut targets use absolute paths with `\\?\` prefix for long Arabic path support

### Unified State

- [ ] **STATE-01**: Single `state.json` per house replaces `1_cleaned`, `2_grouped`, `3_routed` JSONs
- [ ] **STATE-02**: Each entry tracks vault_id, tenant, category, display_name, date, and user_locked status
- [ ] **STATE-03**: `report.json` preserved as raw LLM dump (never modified by downstream logic)
- [ ] **STATE-04**: Atomic writes via `tempfile` + `os.fsync` + `os.replace` for crash safety

### Timeline View

- [ ] **TIMELINE-01**: System generates `00_Timeline_View/` folder per house
- [ ] **TIMELINE-02**: Shortcuts inside `00_Timeline_View/` are numbered chronologically (e.g., `01 - 2010-02-09 - Contract.lnk`)
- [ ] **TIMELINE-03**: Timeline View is regenerated automatically after every reconciliation run
- [ ] **TIMELINE-04**: `finalized.pdf` is no longer generated (replaced by Timeline View)

### Bidirectional Reconciliation

- [ ] **RECON-01**: Reconciliation scans physical folders for `.lnk` shortcuts before applying any logic
- [ ] **RECON-02**: System detects when a user has manually moved a shortcut to a different category folder
- [ ] **RECON-03**: Detected manual moves update `state.json` and flag the document as `user_locked: true`
- [ ] **RECON-04**: User-locked documents are never overridden by AI re-routing
- [ ] **RECON-05**: `reconcile --tenants` re-routes only unlocked documents based on updated `_tenants.yaml` timeline
- [ ] **RECON-06**: Reconciliation regenerates `00_Timeline_View/` after all moves
- [ ] **RECON-07**: Reconciliation detects deleted shortcuts and logs warnings

### Prepend Mode

- [ ] **PREPEND-01**: Rename "append" to "prepend" across all CLI commands, code, and documentation
- [ ] **PREPEND-02**: Prepend mode adds new incoming documents to the vault and generates shortcuts
- [ ] **PREPEND-03**: New documents are prepended (placed at beginning of chronological order) in Timeline View

### Migration

- [ ] **MIGRATE-01**: Migration script converts existing houses from direct-placement to vault format
- [ ] **MIGRATE-02**: Migration preserves current folder structure as user-pinned locations
- [ ] **MIGRATE-03**: Migration includes dry-run mode to preview changes without modifying files

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Grouping Fixes

- **GROUP-01**: Fix name canonicalization to group family members under a single household identity
- **GROUP-02**: Introduce CLI commands for splitting/merging document groups

### Advanced Features

- **ADV-01**: Content-addressing for automatic deduplication of identical PDFs
- **ADV-02**: Use pinned user overrides as few-shot examples for future LLM categorization

## Out of Scope

| Feature | Reason |
|---------|--------|
| Grouping logic changes | Fixing how pages are merged into documents requires LLM prompt redesign — separate milestone |
| Name canonicalization | Family member grouping needs a "Household ID" concept — separate milestone |
| macOS support | This milestone targets Windows only (`.lnk` shortcuts) |
| Real-time file watching for bidirectional sync | Race conditions and debounce complexity — use deterministic polling via `pathlib` instead |
| SQLite database | User chose unified `state.json` — database ORMs are overkill for this use case |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| VAULT-01 | — | Pending |
| VAULT-02 | — | Pending |
| VAULT-03 | — | Pending |
| VAULT-04 | — | Pending |
| VAULT-05 | — | Pending |
| LNK-01 | — | Pending |
| LNK-02 | — | Pending |
| LNK-03 | — | Pending |
| LNK-04 | — | Pending |
| STATE-01 | — | Pending |
| STATE-02 | — | Pending |
| STATE-03 | — | Pending |
| STATE-04 | — | Pending |
| TIMELINE-01 | — | Pending |
| TIMELINE-02 | — | Pending |
| TIMELINE-03 | — | Pending |
| TIMELINE-04 | — | Pending |
| RECON-01 | — | Pending |
| RECON-02 | — | Pending |
| RECON-03 | — | Pending |
| RECON-04 | — | Pending |
| RECON-05 | — | Pending |
| RECON-06 | — | Pending |
| RECON-07 | — | Pending |
| PREPEND-01 | — | Pending |
| PREPEND-02 | — | Pending |
| PREPEND-03 | — | Pending |
| MIGRATE-01 | — | Pending |
| MIGRATE-02 | — | Pending |
| MIGRATE-03 | — | Pending |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 0
- Unmapped: 30 ⚠️

---
*Requirements defined: 2026-07-31*
*Last updated: 2026-07-31 after initial definition*
