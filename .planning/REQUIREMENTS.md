# Requirements: File Organizer Post-Processor

**Defined:** 2026-07-06
**Core Value:** Automatically transform a flat, pre-categorized PDF into a perfectly organized folder structure per tenant, with zero manual sorting — driven entirely by the JSON report data, LLM intelligence, and configurable YAML routing rules.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Config & Scripts Cleanup

- [ ] **CLN-01**: Delete `config.yaml` and `sample-config.yaml` from project root.
- [ ] **CLN-02**: Delete the `scripts/` directory and its contents (`sample-grouping.py`, `sample-routing.py`).

### Core Module Cleanup

- [ ] **CLN-03**: Remove YAML-related config parsing from `src/core/config.py` (`load_user_config`, `InvalidConfigError`).
- [ ] **CLN-04**: Remove deprecated `Config*` schema classes from `src/core/schemas.py`.

### Dead Processing Modules

- [ ] **CLN-05**: Delete `src/processing/extractors.py`.
- [ ] **CLN-06**: Delete `src/processing/ingest.py`.

### Pipeline Orchestrator Cleanup

- [ ] **CLN-07**: Remove the unused `process_pdf` method and its helpers from `src/processing/pipeline.py`.
- [ ] **CLN-08**: Remove unused config arguments from `_group_and_route_documents` in `pipeline.py`.

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### [Category]

- **[CAT]-01**: [Requirement description]
- **[CAT]-02**: [Requirement description]

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| YAML Re-integration | The project specifically moved away from YAML configs to hardcoded routing in v1.0. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLN-01 | Phase 12 | Pending |
| CLN-02 | Phase 12 | Pending |
| CLN-03 | Phase 13 | Pending |
| CLN-04 | Phase 13 | Pending |
| CLN-05 | Phase 14 | Pending |
| CLN-06 | Phase 14 | Pending |
| CLN-07 | Phase 15 | Pending |
| CLN-08 | Phase 15 | Pending |

**Coverage:**
- v1 requirements: 8 total
- Mapped to phases: 8
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-06*
*Last updated: 2026-07-06 after definition*
