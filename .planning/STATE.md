---
gsd_state_version: 1.0
milestone: v4.0
milestone_name: Architectural Cleanup
current_phase: 25
status: pending
stopped_at: Milestone v4.0 initialized
last_updated: "2026-07-24T12:55:00.000Z"
last_activity: 2026-07-24
last_activity_desc: Milestone v4.0 initialized with 5 phases
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 5
  completed_plans: 0
  percent: 0
current_phase_name: extract-presentation-from-core
---

# Project State

**Current Phase:** 25
**Status:** Pending — ready to plan Phase 25

## Phase Progress

- [ ] Phase 25: Extract Presentation Logic from `core/` (ARCH-01)
- [ ] Phase 26: Rename `fs_ui/` to `watcher/` (ARCH-02)
- [ ] Phase 27: Disambiguate Reconciliation Modules (ARCH-03)
- [ ] Phase 28: Clean Up `main.py` Dead Imports (ARCH-04)
- [ ] Phase 29: Audit Test Mock Patch Targets (ARCH-05)

## Open Issues / Blockers

None.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260721-n3z | Implement reconcile --tenants mode in main.py. It should read _tenants.yaml, parse dates, update _1_cleaned.json, _2_grouped.json, and _3_routed.json in-place so canonical_tenant matches the yaml based on dates. Then move PDFs on disk and delete old empty folders. | 2026-07-21 | ac83c4b | [260721-n3z-implement-reconcile-tenants-mode-in-main](./quick/260721-n3z-implement-reconcile-tenants-mode-in-main/) |
| 260724-refactor | Refactor main.py pipeline runner functions to src/pipeline/runner.py, update main.py and orchestrator.py imports, and verify pytest suite execution. | 2026-07-24 | 41c1beb | [260724-refactor-main-pipeline-runner](./quick/260724-refactor-main-pipeline-runner/) |

## Session

**Last session:** 2026-07-24T12:55:00.000Z
**Stopped at:** Milestone v4.0 initialized
**Resume file:** —

## Current Position

Phase: 25 — Extract Presentation from core/
Plan: —
Status: Ready to plan
Last activity: 2026-07-24 — Milestone v4.0 initialized

## Operator Next Steps

- Run `/gsd-plan-phase 25` to plan Phase 25 (Extract `core/ui.py`)
- Or run `/gsd-autonomous` to execute all 5 phases sequentially

## Accumulated Context

### Key Decisions (Milestone v4.0)

- Rejected `domain/` and `infra/` wrapper directories — adds nesting without benefit in a 14-package project
- Rejected `PipelineContext` object — current disk-checkpoint approach is already superior for resumability and debugging
- Rejected splitting `main.py` into separate entry points — single entry with subcommands is the standard pattern
- Chose surgical 5-point cleanup over full hexagonal restructuring

### Roadmap Evolution

- Phase 19.1.1 inserted after Phase 19.1: Close gap: PIPE-02 — Refactor tenant matching logic from tenants.py to grouping/name_matcher.py (URGENT)
- Phase 19.1.1.1 inserted after Phase 19.1.1: Close gap: YAML-01 — Update yaml_loader.py to check root folder .source_files/ for YAML (URGENT)
- Phase 19 reopened 2026-07-17: Test suite overhaul (TEST-01–TEST-06) — naming convention enforcement, golden_1273 fixture restructure, .source_files placement bug, LLM mocking, E2E routing destination assertions
- Phase 24.1 inserted after Phase 24: Update test suite and fixtures for Phase 24 (URGENT)

### Key Decisions (Milestone v3.0)

- Inbox Parser: Used split(maxsplit=5) to separate positional args from title, avoiding complex joins.
- Adopt a hybrid architecture: retain the stateless, functional approach for the core document pipeline, but introduce class-based orchestrators for the stateful, long-running FS-UI listener in upcoming phases.

## Performance Metrics

| Phase | Plan | Duration | Notes |
|-------|------|----------|-------|
| Phase 19.1.1 P1 | 10 min | 3 tasks | 6 files |
| Phase 22 P03 | 1 min | 1 tasks | 3 files |
| Phase 23 P01 | 15 min | 3 tasks | 3 files |
| Phase 24 P02 | 15 min | 2 tasks | 5 files |

## Deferred Items

Items acknowledged and deferred at milestone close on 2026-07-17:

| Category | Item | Status |
|----------|------|--------|
| Phase 19 | TEST-02: Restructure golden_1273 fixture folders | Deferred |
| Phase 19 | TEST-03: Fix .source_files placement inside house directory | Deferred |
| Phase 19 | TEST-04: Add intermediate JSON state files to golden fixture | Deferred |
| Phase 19 | TEST-05: Implement function-level LLM mocking | Deferred |
| Phase 19 | TEST-06: Add E2E routing destination assertions | Deferred |
