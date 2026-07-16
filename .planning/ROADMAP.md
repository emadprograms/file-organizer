# Roadmap: File Organizer Refactoring

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-07-08)
- ✅ **v1.1 Logging Overhaul** — Phase 4-6 (shipped 2026-07-08) [Archive: .planning/milestones/v1.1-ROADMAP.md]
- ✅ **v1.2 Pipeline Resilience & Grouping Overhaul** — Phases 7-10 (shipped 2026-07-10) [Archive: .planning/milestones/v1.2-ROADMAP.md]
- ✅ **v1.3 Routing Decoupling & Checkpointing** — Phases 11-13 (shipped 2026-07-10) [Archive: .planning/milestones/v1.3-ROADMAP.md]
- 🛑 **v1.4 LLM Performance & Optimization** — Phases 14-15 (Archived)
- 🚧 **v2.0 Logic-Based Modular Refactoring** — Phases 16-19 (planned)

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

<details>
<summary>✅ v1.3 Routing Decoupling & Checkpointing (Phases 11-13) — SHIPPED 2026-07-10</summary>

- [x] Phase 11: Conditional LLM Folder Routing and Folder Renaming
- [x] Phase 12: Finalize Conditional LLM Folder Routing and Folder Renaming (0 plans)
- [x] Phase 13: Routing Checkpoints & Architecture Decoupling
  **Goal:** Fix the routing result data loss bug, resolve implicit model propagation, and complete the architecture decoupling of routing from grouping.
  **Plans:** 3 plans
  Plans:

  - [x] 13-01-PLAN.md — Refactor state schema and config for result persistence
  - [x] 13-02-PLAN.md — Decouple pipeline and fix routing resumption bug
  - [x] 13-03-PLAN.md — Implement E2E verification for resilience and model propagation

</details>

### 🛑 v1.4 LLM Performance & Optimization (Archived)

Archived to proceed with v2.0 Refactoring.

### 🚧 v2.0 Logic-Based Modular Refactoring

- [x] Phase 16: Setup New Directory Structure
  **Goal:** Reorganize `src/` into logical folders (core, utils, tenant_config, grouping, timeline, routing) preserving all existing files.

- [ ] Phase 16.1: Cleanup Checkpoints System
  **Goal:** Refactor the confusing checkpoint system (checkpoints folder, cleaned json, manifest.json).

- [x] Phase 17: Implement YAML Configuration Loading (tenant_config) (1/1 plans)
  **Goal:** Create logic to find the root folder "source files" and extract primary tenant names.

- [x] Phase 18: Refactor Pipeline to use YAML (grouping, timeline, routing)
  **Goal:** Remove anchor logic and use YAML tenant names for Pass 1 LLM extraction. Connect the rest of the existing modules.

- [x] Phase 18.5: Finalize PDF Output, Compression, and Metadata
  **Goal:** Compress the original `_categorized` PDF to normal quality. Ensure the final routed PDF is both compressed and labeled `_finalized` (instead of `_categorized`). Update the PDF metadata to explicitly show "Tenant - Folder Name" (e.g., "1273 - folder_name") rather than just the category.
  **Plans:** 1 plan
  Plans:

  - [x] 18.5-01-PLAN.md — Finalize PDF Output, Compression, and Metadata
- [x] Phase 18.6: Fix Fallback Model Behavior Across Codebase
  **Goal:** Update LLM error handling for read timeouts and 429s globally. After 3 failures on the default model, drop down to Gemini 3.5 Flash -> Gemini 3 Flash -> Gemini 2.5 Flash without waiting for multiple retries on the Flash models. Apply this logic uniformly across the codebase.

- [x] Phase 19: End-to-End Testing and Verification (completed 2026-07-16)
  **Goal:** Ensure the pipeline produces the exact same end-to-end results using the new architecture.

- [x] Phase 19.1: Fix YAML Integration Architecture (completed 2026-07-16)
  **Goal:** Refactor the pipeline to properly utilize `yaml_loader.py` for configuration loading and remove dead code, properly connecting it to `pipeline.py` instead of bypassing it in `phase.py`.

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
| 12. Finalize Conditional LLM Folder Routing and Folder Renaming | v1.3 | 0/0 | Complete | 2026-07-10 |
| 13. Routing Checkpoints & Architecture Decoupling | v1.3 | 3/3 | Complete | 2026-07-10 |
| 14. Parallel Pipeline Refactoring | v1.4 | 0/0 | Archived | — |
| 15. LLM Client Resilience & Failover Fixes | v1.4 | 0/0 | Archived | — |
| 16. Setup New Directory Structure | v2.0 | 0/0 | Complete | 2026-07-15 |
| 16.1. Cleanup Checkpoints System | v2.0 | 1/1 | Complete | 2026-07-15 |
| 17. Implement YAML Configuration Loading | v2.0 | 1/1 | Complete | 2026-07-15 |
| 18. Refactor Pipeline to use YAML | v2.0 | 2/2 | Complete | 2026-07-15 |
| 18.5. Finalize PDF Output, Compression, and Metadata | v2.0 | 1/1 | Complete | 2026-07-15 |
| 18.6. Fix Fallback Model Behavior Across Codebase | v2.0 | 0/0 | Complete | 2026-07-15 |
| 19. End-to-End Testing and Verification | v2.0 | 1/1 | Complete    | 2026-07-16 |
| 19.1. Fix YAML Integration Architecture | v2.0 | 1/1 | Complete   | 2026-07-16 |
