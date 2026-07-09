# Roadmap: File Organizer Refactoring

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-07-08)
- ✅ **v1.1 Logging Overhaul** — Phase 4-6 (shipped 2026-07-08) [Archive: .planning/milestones/v1.1-ROADMAP.md]
- 🔄 **v1.2 Pipeline Resilience & Grouping Overhaul** — Phases 7-10 (Current)

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

### v1.2 Pipeline Resilience & Grouping Overhaul (Current)

- [x] **Phase 7: Anti-Hallucination Schema Enforcement**
  - Depends on: None
  - Requirements: SCHM-01
  - Success Criteria:
    - [x] System rejects router responses that contain invalid folder paths automatically.
    - [x] Router uses Pydantic literal types based on the user's specific folder structure instead of arbitrary strings.
    - [x] Pipeline logs validation errors correctly when avoiding mis-routed documents.

  Plans:

  - [x] 07-01-PLAN.md — Implement dynamic routing schema enforcement using Pydantic create_model
  - [x] 07-02-PLAN.md — Integrate dynamic schema and implement feedback-driven retry loop
  - [x] 07-03-PLAN.md — Integration audit and test suite update

- [x] **Phase 8: "True Until Proven Guilty" Grouping Logic**
  - Depends on: None
  - Requirements: PRMPT-01, PRMPT-02, PRMPT-03
  - Success Criteria:
    - [x] Documents containing continuation letters across page boundaries are correctly grouped together.
    - [x] Un-headered tables and appendices spanning multiple pages are not incorrectly split.
    - [x] System groups chunks into larger logical files unless explicit proof of distinct topics is found.

- [x] **Phase 9: Rate Limiting & Router Safety Net** (completed 2026-07-09)
  - Depends on: 7
  - Requirements: RES-01, RES-02, RES-03
  - Success Criteria:
    - [x] System pauses and gracefully retries upon encountering rate limiting, instead of crashing.
    - [x] Critical runtime errors immediately halt the pipeline.
    - [x] A single routing failure does not cause a permanent lockout for subsequent routing requests.

- [ ] **Phase 10: Chunk State Management**
  - Depends on: 8, 9
  - Requirements: GRP-01, GRP-02, GRP-03, GRP-04
  - Success Criteria:
    - [ ] Grouping mechanism processes pages in chunks of 5, 3, then 2 upon consecutive failures.
    - [ ] Exhausting grouping attempts gracefully halts the pipeline, enabling checkpoint resuming.
    - [ ] Chunk success correctly resets the chunk size index to 0.
    - [ ] Merged documents respect logical boundaries without arbitrary overlap merging.

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
| 8. "True Until Proven Guilty" Grouping Logic | v1.2 | 0/0 | Pending | — |
| 9. Rate Limiting & Router Safety Net | v1.2 | 3/2 | Complete    | 2026-07-09 |
| 10. Chunk State Management | v1.2 | 0/0 | Pending | — |
