# Roadmap: File Organizer Refactoring

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-07-08)
- ✅ **v1.1 Logging Overhaul** — Phase 4-6 (shipped 2026-07-08) [Archive: .planning/milestones/v1.1-ROADMAP.md]
- ✅ **v1.2 Pipeline Resilience & Grouping Overhaul** — Phases 7-10 (shipped 2026-07-10) [Archive: .planning/milestones/v1.2-ROADMAP.md]
- 🚧 **v1.3 Routing Decoupling & Checkpointing** — Phases 11-13 (planned)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-3) — SHIPPED 2026-07-08</summary>

- [x] Phase 1: Legacy Code Cleanup (1/1 plans) — completed 2026-07-07
- [x] Phase 2: Refactor src/cleaning.py (1/1 plans) — completed 2026-07-08
- [x] Phase 3: Refactor Processing and Oversized Functions (5/5 plans) — completed 2026-07-08

</details>

<details>
<summary>✅ v1.1 Logging Overhaul (Phase 4-6) — SHIPPED 2026-07-08</summary>

- [x] Phase 4: Logging Infrastructure Refactor (1/1 plans)
- [x] Phase 5: Global Logger Migration (4/4 plans)
  Plans:

  - [x] 05-01-PLAN.md — Standardize hierarchical loggers and variable names
  - [x] 05-02-PLAN.md — Convert telemetry print() statements to loggers
  - [x] 05-03-PLAN.md — Separate UI (Rich) from telemetry and sync verbosity
  - [x] 05-04-PLAN.md — End-to-end logging audit and verification

- [x] Phase 6: Validation and Audit (1/1 plans) — completed 2026-07-08
  Depends on: 4, 5

</details>

<details>
<summary>✅ v1.2 Pipeline Resilience & Grouping Overhaul (Phases 7-10) — SHIPPED 2026-07-10</summary>

- [x] Phase 7: Anti-Hallucination Schema Enforcement (3/3 plans) — completed 2026-07-08
- [x] Phase 8: "True Until Proven Guilty" Grouping Logic (4/4 plans) — completed 2026-07-10
- [x] Phase 9: Rate Limiting & Router Safety Net (2/2 plans) — completed 2026-07-09
- [x] Phase 10: Chunk State Management (4/4 plans) — completed 2026-07-10

</details>

### 🚧 v1.3 Routing Decoupling & Checkpointing

- [x] Phase 11: Conditional LLM Folder Routing and Folder Renaming
- [ ] Phase 12: Finalize Conditional LLM Folder Routing and Folder Renaming (0 plans)
- [ ] Phase 13: Routing Checkpoints & Architecture Decoupling
  **Goal:** Fix the routing result data loss bug, resolve implicit model propagation, and complete the architecture decoupling of routing from grouping.
  **Plans:** 3 plans
  Plans:
  - [ ] 13-01-PLAN.md — Refactor state schema and config for result persistence
  - [ ] 13-02-PLAN.md — Decouple pipeline and fix routing resumption bug
  - [ ] 13-03-PLAN.md — Implement E2E verification for resilience and model propagation

## Progress

| Phase             | Milestone | Plans Complete | Status      | Completed  |
| ----------------- | --------- | -------------- | ----------- | ---------- |
| 1. Legacy Code Cleanup | v1.0 | 1/1 | Complete | 2026-07-07 |
| 2. Refactor src/cleaning.py | v1.0 | 1/1 | Complete | 2026-07-08 |
| 3. Refactor Processing and Oversized Functions | v1.0 | 5/5 | Complete | 2026-07-08 |
| 4. Logging Infrastructure Refactor | v1.1 | 1/1 | Complete | 2026-07-08 |
| 5. Global Logger Migration | v1.1 | 4/4 | Complete | 2026-07-08 |
| 6. Validation and Audit | v1.1 | 1/1 | Complete | 2026-07-08 |
| 7. Anti-Hallucination Schema Enforcement | v1.2 | 3/3 | Complete | 2026-07-08 |
| 8. "True Until Proven Guilty" Grouping Logic | v1.2 | 4/4 | Complete | 2026-07-10 |
| 9. Rate Limiting & Router Safety Net | v1.2 | 2/2 | Complete    | 2026-07-09 |
| 10. Chunk State Management | v1.2 | 4/4 | Complete | 2026-07-10 |
| 11. Conditional LLM Folder Routing and Folder Renaming | v1.3 | -/- | Complete | 2026-07-10 |
| 12. Finalize Conditional LLM Folder Routing and Folder Renaming | v1.3 | 0/0 | Pending | — |
| 13. Routing Checkpoints & Architecture Decoupling | v1.3 | 0/0 | Pending | — |
