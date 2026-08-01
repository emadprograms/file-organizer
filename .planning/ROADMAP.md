# Roadmap: File Organizer Refactoring

## Milestones

- ✅ **v3.0 Unified File-System UI & Append Mode** — Phases 20-24.1 (shipped 2026-07-24)
- ✅ **v4.0 Architectural Cleanup** — Phases 25-29.1 (shipped 2026-07-31)
- ✅ **v5.0 Vault Architecture & Bidirectional Reconciliation** — Phases 30-35 (shipped 2026-08-01)
- ✅ **v5.1 Polishing & Migration Cleanup** — Phases 36-38 (shipped 2026-08-01)
- ✅ **v5.2 Deep Architecture Integrity & Verification** — Phases 39-42 (shipped 2026-08-01)
- 🔄 **v5.3 Reconciliation Engine Upgrade** — Phases 43-47

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

<details>
<summary>✅ v5.0 Vault Architecture & Bidirectional Reconciliation (Phases 30-35) — SHIPPED 2026-08-01</summary>

See [.planning/milestones/v5.0-ROADMAP.md](milestones/v5.0-ROADMAP.md) for full phase details.

</details>

<details>
<summary>✅ v5.1 Polishing & Migration Cleanup (Phases 36-38) — SHIPPED 2026-08-01</summary>

See [.planning/milestones/v5.1-ROADMAP.md](milestones/v5.1-ROADMAP.md) for full phase details.

</details>

<details>
<summary>✅ v5.2 Deep Architecture Integrity & Verification (Phases 39-42) — SHIPPED 2026-08-01</summary>

### Phase 39: Verification Module Scaffolding & CLI Integration

**Requirements:** REQ-01
**Success Criteria:** `src/core/verification.py` is created. `main.py` CLI exposes `file-organizer verify`. Basic structural checking is wired up.

### Phase 40: Vault & Shortcut Resolution Engine

**Requirements:** REQ-02
**Success Criteria:** The verifier recursively parses `.lnk` files in categorized directories and `[Timeline View]`, validating their absolute targets against the vault.

### Phase 41: State & YAML Integrity Rules

**Requirements:** REQ-03, REQ-04
**Success Criteria:** The verifier cross-references `state.json` against actual folder layout. Orphan PDFs in the vault are detected. Ghost legacy JSONs and physical PDFs outside the vault are flagged. Tenant structures match `tenants.yaml`.

### Phase 42: Comprehensive Test Suite

**Requirements:** REQ-05
**Success Criteria:** `pytest` tests are added for the verification module handling various valid and corrupt state scenarios.

</details>

### 🔄 v5.3 Reconciliation Engine Upgrade (Phases 43-47)

### Phase 43: Ghost File Adoption & Raw PDF Ingestion

**Requirements:** REQ-01, REQ-03
**Success Criteria:** The reconciler detects physical shortcuts and raw PDFs on disk that have no `state.json` entry, formally adopts them (assigns vault_id, extracts date from filename, creates per_page entry), and moves raw PDFs into the vault with shortcuts in their place. Zero unaccounted files after reconciliation.

### Phase 44: User Deletion & Orphan Cleanup

**Requirements:** REQ-02
**Success Criteria:** The reconciler detects deleted shortcuts, removes their `state.json` entries, and moves the corresponding vault PDFs to `.source_files/.trash/` for recovery. No orphan vault PDFs remain after reconciliation.

### Phase 45: Duplicate Shortcuts & Renamed Shortcuts

**Requirements:** REQ-04, REQ-05
**Success Criteria:** The reconciler handles multiple shortcuts pointing to the same vault PDF (1-to-many) without errors. Renamed shortcuts are detected and `state.json` is updated to match, with `user_locked: true` applied.

### Phase 46: Auto-Verification & Reconciliation Report

**Requirements:** REQ-06, REQ-07
**Success Criteria:** `run_verification()` runs automatically after every reconciliation. A structured JSON report is saved to `.source_files/` summarizing all actions taken (adopted, deleted, moved, renamed, verification pass/fail). Console prints a human-readable summary.

### Phase 47: Reconciliation Test Suite

**Requirements:** REQ-08
**Success Criteria:** `pytest` tests cover all edge cases: ghost files, user deletions, raw PDF drops, duplicate shortcuts, renames, auto-verification integration. Each scenario validates that `state.json` is correctly updated.

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
| 30. Unified State Foundation | v5.0 | 1/1 | Complete    | 2026-07-31 |
| 31. Vault Core & Shortcut Utility | v5.0 | 1/1 | Complete    | 2026-07-31 |
| 32. Pipeline Migration | v5.0 | 1/0 | Complete    | 2026-07-31 |
| 33. Bidirectional Reconciliation Engine | v5.0 | 1/1 | Complete    | 2026-07-31 |
| 34. Prepend Mode | v5.0 | 1/0 | Complete    | 2026-07-31 |
| 35. Migration Script | v5.0 | 1/0 | Complete    | 2026-07-31 |
| 36. Environment & E2E Testing | v5.1 | 1/1 | Complete | 2026-08-01 |
| 37. Timeline View UX Improvements | v5.1 | 1/1 | Complete | 2026-08-01 |
| 38. Unified State Migration | v5.1 | 1/1 | Complete | 2026-08-01 |
| 39. Verification Scaffolding | v5.2 | 1/1 | Complete | 2026-08-01 |
| 40. Vault & Shortcut Engine | v5.2 | 1/1 | Complete | 2026-08-01 |
| 41. State & YAML Rules | v5.2 | 1/1 | Complete | 2026-08-01 |
| 42. Comprehensive Test Suite | v5.2 | 1/1 | Complete | 2026-08-01 |
| 43. Ghost File Adoption & Raw PDF Ingestion | v5.3 | 1/1 | Complete | 2026-08-01 |
| 44. User Deletion & Orphan Cleanup | v5.3 | 1/1 | Complete | 2026-08-01 |
| 45. Duplicate Shortcuts & Renamed Shortcuts | v5.3 | 1/1 | Complete | 2026-08-01 |
| 46. Auto-Verification & Reconciliation Report | v5.3 | 0/0 | Planned | — |
| 47. Reconciliation Test Suite | v5.3 | 0/0 | Planned | — |



