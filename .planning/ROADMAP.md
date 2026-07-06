# Roadmap: File Organizer Post-Processor

**Created:** 2026-07-03
**Phases:** 5
**Structure:** Horizontal Layers (Foundation → Pass 1 → Pass 2 → Output → Polish)

---

## Milestone: v1.0 (Complete)
- **Status:** Shipped 2026-07-06. Full pipeline implementation from ingest to physical organization. [See Archive](milestones/v1.0-ROADMAP.md)

---

## Phase Dependencies

---

## Phase Dependencies

```
Phase 1 (Foundation) ──→ Phase 2 (Pass 1) ──→ Phase 3 (Pass 2) ──→ Phase 4 (Output) ──→ Phase 5 (Polish) ──→ Phase 6 (Gap Closures)
```

All phases are strictly sequential — each depends on the previous.

---

## Requirement Coverage

| 01 | Requirements & Architecture | Complete | 2026-07-04 | 1 | 1 |
| 02 | Parsing & Pass 1 Cleaning | Complete | 2026-07-04 | 2 | 2 |
| 03 | Pass 2 Grouping & Routing | Complete | 2026-07-04 | 2 | 2 |
| 04 | Output Structure & Reconciliation | Complete | 2026-07-05 | 2 | 2 |
| 05 | Dry Run & Polish | Pending | - | 0 | 0 |

| Requirement | Phase |
|-------------|-------|
| INIT-01 through INIT-07 | Phase 1 |
| LLM-01 through LLM-09 | Phase 1 |
| LOG-01 through LOG-03 | Phase 1 |
| FS-01 through FS-04 | Phase 1 |
| CLN-01 through CLN-10 | Phase 2 |
| GRP-01 through GRP-13 | Phase 3 |
| OUT-01 through OUT-06 | Phase 4 |
| LOG-04 | Phase 4 |
| DIFF-02, DIFF-03 | Phase 4 |
| DIFF-01 | Phase 5 |

**Coverage:** 48/48 requirements mapped ✓
**Unmapped:** 0 ✓

### Phase 7: Cross-Phase Integration Fixes — tenant/date mapping, relative indexing, CLI flags, dry-run safety

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 6
**Plans:** 0 plans

Plans:

- [ ] TBD (run /gsd-plan-phase 7 to break down)

### [x] Phase 8: Address tech debt: test assertions for logs/fallback

**Goal:** Address tech debt: test assertions for logs/fallback
**Requirements**: Verify fallback/retry logic emits correct log warnings
**Depends on:** Phase 7
**Plans:** 4 plans

Plans:

- [x] 1. Upgrade Log Levels in `llm.py`
- [x] 2. Add Caplog Assertions to Fallback Tests
- [x] 3. Add Caplog Assertions to LLM Retry Tests
- [x] 4. Verify the Test Suite Passes

### [x] Phase 9: Final E2E Sweep: Fix absolute PDF indexing, array bounds alignment, resolved dates, LLM logging, and pipeline architecture

**Goal:** Final E2E Sweep: Fix absolute PDF indexing, array bounds alignment, resolved dates, LLM logging, and pipeline architecture
**Requirements**: CLN-08, GRP-06, LOG-02, OUT-06
**Depends on:** Phase 8
**Plans:** 1/1 plans complete

Plans:

- [x] 1. Core Implementation and Verification

### [x] Phase 10: Close gaps: Wire correct sanitize_filename and fix LLM 500 error handling

**Goal:** Standardize `sanitize_filename` across the project to ensure file extensions are preserved while maintaining safety truncations. Implement a global LLM 500 error counter to abort the pipeline cleanly upon persistent failure.
**Requirements**: None
**Depends on:** Phase 9
**Plans:** 1/1 plans complete

Plans:

- [x] 1. Core Implementation and Verification

### Phase 11: Close gaps: LLM-01 to LLM-08, LOG-02, OUT-05, GRP-10 — Wire correct LLMClient error handling, audit logging, unassigned folder naming, and semantic routing

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 10
**Plans:** 1/1 plans complete

Plans:

- [x] TBD (run /gsd-plan-phase 11 to break down) (completed 2026-07-06)

---
*Roadmap created: 2026-07-03*
*Last updated: 2026-07-03 after initial creation*
