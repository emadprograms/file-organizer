# Roadmap: File Organizer Refactoring

## Milestones

- ✅ **v3.0 Unified File-System UI & Append Mode** — Phases 20-24.1 (shipped 2026-07-24)
- ✅ **v4.0 Architectural Cleanup** — Phases 25-29.1 (shipped 2026-07-31)
- 🚧 **v5.0 Vault Architecture & Bidirectional Reconciliation** — Phases 30-35 (in progress)

## Phases

<details>
<summary>✅ v3.0 Unified File-System UI & Append Mode (Phases 20-24.1) — SHIPPED 2026-07-24</summary>

- [x] Phase 20: Codebase Maintainability Sweep (3/3 plans) — completed 2026-07-18
- [x] Phase 21: System Unification (1/1 plan) — completed 2026-07-20
- [x] Phase 22: Configuration and CLI Modes (3/3 plans) — completed 2026-07-20
- [x] Phase 23: Inbox Parsing and Syntax (2/2 plans) — completed 2026-07-20
- [x] Phase 24: FS-UI Orchestration (4/4 plans) — completed 2026-07-20
- [x] Phase 24.1: Update test suite and fixtures for Phase 24 (4/4 plans) — completed 2026-07-23

</details>

<details>
<summary>✅ v4.0 Architectural Cleanup (Phases 25-29.1) — SHIPPED 2026-07-31</summary>

- [x] Phase 25: Extract Presentation Logic from `core/` (ARCH-01) - completed 2026-07-24
- [x] Phase 26: Rename `fs_ui/` to `watcher/` (ARCH-02) - completed 2026-07-24
- [x] Phase 27: Disambiguate Reconciliation Modules (ARCH-03) - completed 2026-07-24
- [x] Phase 28: Clean Up `main.py` Dead Imports (ARCH-04) - completed 2026-07-24
- [x] Phase 29: Audit Test Mock Patch Targets (ARCH-05) - completed 2026-07-24
- [x] Phase 29.1: Fix Append-Mode Finalize Bugs (URGENT) - completed 2026-07-31

</details>

### 🚧 v5.0 Vault Architecture & Bidirectional Reconciliation

### Phase 30: Unified State Foundation
**Requirements:** STATE-01, STATE-02, STATE-03, STATE-04
**Success Criteria:** Single `state.json` is created per house, legacy multi-json checkpoints are not generated, system continues to run crash-safe writes.

### Phase 31: Vault Core & Shortcut Utility
**Requirements:** VAULT-01, VAULT-02, VAULT-03, VAULT-04, VAULT-05, LNK-01, LNK-02, LNK-03, LNK-04
**Success Criteria:** Physical PDFs are copied to `.source_files/vault/` with UUIDs, Windows `.lnk` shortcuts are successfully generated using pylnk3, Shortcuts open the correct vault PDF targets.

### Phase 32: Pipeline Migration
**Requirements:** TIMELINE-01, TIMELINE-02, TIMELINE-03, TIMELINE-04
**Success Criteria:** `00_Timeline_View/` folder is generated containing numbered shortcuts, `finalized.pdf` is no longer created, Main pipeline output uses shortcuts instead of physical PDFs.

### Phase 33: Bidirectional Reconciliation Engine
**Requirements:** RECON-01, RECON-02, RECON-03, RECON-04, RECON-05, RECON-06, RECON-07
**Success Criteria:** Manually moved shortcuts trigger `user_locked: true` in `state.json`, Reconciliation re-routes unlocked documents based on `_tenants.yaml`, Timeline View is regenerated after moves.

### Phase 34: Prepend Mode
**Requirements:** PREPEND-01, PREPEND-02, PREPEND-03
**Success Criteria:** "append" is renamed to "prepend" across the app, Prepend mode adds incoming documents to the vault, New documents appear at the beginning of Timeline View.

### Phase 35: Migration Script
**Requirements:** MIGRATE-01, MIGRATE-02, MIGRATE-03
**Success Criteria:** Dry-run script lists changes without modifying files, Migration converts existing structured folders to vault format and pins locations.

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 20. Codebase Maintainability Sweep | v3.0 | 3/3 | Complete | 2026-07-18 |
| 21. System Unification | v3.0 | 1/1 | Complete | 2026-07-20 |
| 22. Configuration and CLI Modes | v3.0 | 3/3 | Complete | 2026-07-20 |
| 23. Inbox Parsing and Syntax | v3.0 | 2/2 | Complete | 2026-07-20 |
| 24. FS-UI Orchestration | v3.0 | 4/4 | Complete | 2026-07-20 |
| 24.1. Test Suite & Fixtures Update | v3.0 | 4/4 | Complete | 2026-07-23 |
| 25. Extract Presentation from core/ | v4.0 | 1/1 | Complete | 2026-07-24 |
| 26. Rename fs_ui/ to watcher/ | v4.0 | 1/1 | Complete | 2026-07-24 |
| 27. Disambiguate Reconciliation | v4.0 | 1/1 | Complete | 2026-07-24 |
| 28. Clean Up main.py Imports | v4.0 | 1/1 | Complete | 2026-07-24 |
| 29. Audit Test Mock Targets | v4.0 | 1/1 | Complete | 2026-07-24 |
| 29.1. Fix Append-Mode Finalize Bugs | v4.0 | 1/1 | Complete | 2026-07-31 |
| 30. Unified State Foundation | v5.0 | 1/1 | Complete | 2026-07-31 |
| 31. Vault Core & Shortcut Utility | v5.0 | 1/1 | Complete | 2026-07-31 |
| 32. Pipeline Migration | v5.0 | 0/0 | Not Started | — |
| 33. Bidirectional Reconciliation Engine | v5.0 | 0/0 | Not Started | — |
| 34. Prepend Mode | v5.0 | 0/0 | Not Started | — |
| 35. Migration Script | v5.0 | 0/0 | Not Started | — |
