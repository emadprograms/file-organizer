# Requirements: v5.0 Vault Architecture & Bidirectional Reconciliation

**Defined:** 2026-07-31
**Core Value:** Documents are safely stored once in an immutable vault; all organization is done via lightweight shortcuts that can be freely rearranged by the user without risk of data loss.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Vault Storage

 - [x] **VAULT-01**: System creates a hidden `.source_files/vault/` directory per house
 - [x] **VAULT-02**: Each document group receives a unique UUID
 - [x] **VAULT-03**: Physical PDFs are stored in vault named by UUID (e.g., `doc_A1B2.pdf`)
 - [x] **VAULT-04**: Vault uses two-phase commit (`.tmp` → rename) to prevent orphans on crash
 - [x] **VAULT-05**: Once a PDF enters the vault it is never moved or renamed

### Windows Shortcuts

 - [x] **LNK-01**: System generates Windows `.lnk` shortcut files using `pylnk3` (pure Python, cross-platform testable)
 - [x] **LNK-02**: Shortcuts placed in categorized Arabic folders (e.g., `10_صيانة/`)
 - [x] **LNK-03**: Shortcuts named with date and document title for readability
 - [x] **LNK-04**: Shortcut targets use absolute paths with `\\?\` prefix for long Arabic path support

### Unified State

 - [x] **STATE-01**: Single `state.json` per house replaces `1_cleaned`, `2_grouped`, `3_routed` JSONs
 - [x] **STATE-02**: Each entry tracks vault_id, tenant, category, display_name, date, and user_locked status
 - [x] **STATE-03**: `report.json` preserved as raw LLM dump (never modified by downstream logic)
 - [x] **STATE-04**: Atomic writes via `tempfile` + `os.fsync` + `os.replace` for crash safety

### Timeline View

 - [x] **TIMELINE-01**: System generates `00_Timeline_View/` folder per house
 - [x] **TIMELINE-02**: Shortcuts inside `00_Timeline_View/` are numbered chronologically (e.g., `01 - 2010-02-09 - Contract.lnk`)
 - [x] **TIMELINE-03**: Timeline View is regenerated automatically after every reconciliation run
 - [x] **TIMELINE-04**: `finalized.pdf` is no longer generated (replaced by Timeline View)

### Bidirectional Reconciliation

 - [x] **RECON-01**: Reconciliation scans physical folders for `.lnk` shortcuts before applying any logic
 - [x] **RECON-02**: System detects when a user has manually moved a shortcut to a different category folder
 - [x] **RECON-03**: Detected manual moves update `state.json` and flag the document as `user_locked: true`
 - [x] **RECON-04**: User-locked documents are never overridden by AI re-routing
 - [x] **RECON-05**: `reconcile --tenants` re-routes only unlocked documents based on updated `_tenants.yaml` timeline
 - [x] **RECON-06**: Reconciliation regenerates `00_Timeline_View/` after all moves
 - [x] **RECON-07**: Reconciliation detects deleted shortcuts and logs warnings

### Prepend Mode

 - [x] **PREPEND-01**: Rename "append" to "prepend" across all CLI commands, code, and documentation
 - [x] **PREPEND-02**: Prepend mode adds new incoming documents to the vault and generates shortcuts
 - [x] **PREPEND-03**: New documents are prepended (placed at beginning of chronological order) in Timeline View

### Migration

 - [x] **MIGRATE-01**: Migration script converts existing houses from direct-placement to vault format
 - [x] **MIGRATE-02**: Migration preserves current folder structure as user-pinned locations
 - [x] **MIGRATE-03**: Migration includes dry-run mode to preview changes without modifying files

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
| VAULT-01 | 31 | Mapped |
| VAULT-02 | 31 | Mapped |
| VAULT-03 | 31 | Mapped |
| VAULT-04 | 31 | Mapped |
| VAULT-05 | 31 | Mapped |
| LNK-01 | 31 | Mapped |
| LNK-02 | 31 | Mapped |
| LNK-03 | 31 | Mapped |
| LNK-04 | 31 | Mapped |
| STATE-01 | 30 | Mapped |
| STATE-02 | 30 | Mapped |
| STATE-03 | 30 | Mapped |
| STATE-04 | 30 | Mapped |
| TIMELINE-01 | 32 | Mapped |
| TIMELINE-02 | 32 | Mapped |
| TIMELINE-03 | 32 | Mapped |
| TIMELINE-04 | 32 | Mapped |
| RECON-01 | 33 | Mapped |
| RECON-02 | 33 | Mapped |
| RECON-03 | 33 | Mapped |
| RECON-04 | 33 | Mapped |
| RECON-05 | 33 | Mapped |
| RECON-06 | 33 | Mapped |
| RECON-07 | 33 | Mapped |
| PREPEND-01 | 34 | Mapped |
| PREPEND-02 | 34 | Mapped |
| PREPEND-03 | 34 | Mapped |
| MIGRATE-01 | 35 | Mapped |
| MIGRATE-02 | 35 | Mapped |
| MIGRATE-03 | 35 | Mapped |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0 ✅

---
*Requirements defined: 2026-07-31*
*Last updated: 2026-07-31 after initial definition*
