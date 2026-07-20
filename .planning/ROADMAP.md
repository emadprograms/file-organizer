## Proposed Roadmap

**5 phases** | **12 requirements mapped** | All covered ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 20 | Codebase Maintainability Sweep | 3/3 | Complete    | 2026-07-18 |
| 21 | System Unification | 1/1 | Complete    | 2026-07-20 |
| 22 | Configuration and CLI Modes | 3/3 | Complete   | 2026-07-20 |
| 23 | Inbox Parsing and Syntax | Build parser for space-separated FS-UI commands | FSUI-01, FSUI-02, FSUI-03 | 3 |
| 24 | FS-UI Orchestration | Wire up the rename loop and finalize filing logic | FSUI-04, FSUI-05 | 3 |

### Phase 20: Codebase Maintainability Sweep

**Goal:** Add type hinting and docstrings to v2.0 modules
**Requirements:** MAINT-01
**Depends on:** Phase 19
**Plans:** 3/3 plans complete

Plans:

- [x] 1-domain-and-orchestration-PLAN.md
- [x] 2-pipeline-logic-PLAN.md
- [x] 3-tests-type-hinting-PLAN.md

- [x] TBD (run /gsd-plan-phase 20 to break down) (completed 2026-07-18)

### Phase 21: System Unification

**Goal:** Port file-categorizer logic for `_report.json` generation
**Requirements:** CAT-01, CAT-02
**Depends on:** Phase 20
**Plans:** 1/1 plans complete

Plans:

- [x] 21-PLAN.md (completed 2026-07-19)

### Phase 22: Configuration and CLI Modes (Completed)

**Goal:** Create config.yaml and setup explicit CLI commands
**Requirements:** CONF-01, CONF-02, CONF-03
**Depends on:** Phase 21
**Plans:** 3/3 plans complete

Plans:
**Wave 1**

- [x] 22-01-PLAN.md — Configuration Management

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 22-02-PLAN.md — CLI Subparsers & Process Lock
- [x] 22-03-PLAN.md — Gap Closure: Enforce Test Naming

### Phase 23: Inbox Parsing and Syntax

**Goal:** Build parser for space-separated FS-UI commands
**Requirements:** FSUI-01, FSUI-02, FSUI-03
**Depends on:** Phase 22
**Plans:** 0 plans

Plans:

- [ ] TBD (run /gsd-plan-phase 23 to break down)

### Phase 24: FS-UI Orchestration

**Goal:** Wire up the rename loop and finalize filing logic
**Requirements:** FSUI-04, FSUI-05, FSUI-06
**Depends on:** Phase 23
**Plans:** 0 plans

Plans:

- [ ] TBD (run /gsd-plan-phase 24 to break down)
