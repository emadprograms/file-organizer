# Roadmap: File Organizer Refactoring

## Milestones

- ✅ **v3.0 Unified File-System UI & Append Mode** — Phases 20-24.1 (shipped 2026-07-24)
- ✅ **v4.0 Architectural Cleanup** — Phases 25-29.1 (shipped 2026-07-31)
- ✅ **v5.0 Vault Architecture & Bidirectional Reconciliation** — Phases 30-35 (shipped 2026-08-01)
- ✅ **v5.1 Polishing & Migration Cleanup** — Phases 36-38 (shipped 2026-08-01)
- ✅ **v5.2 Deep Architecture Integrity & Verification** — Phases 39-42 (shipped 2026-08-01)

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

### ✅ v5.2 Deep Architecture Integrity & Verification (Phases 39-42) — SHIPPED 2026-08-01

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
