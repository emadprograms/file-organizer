# Requirements: v5.1 Polishing & Migration Cleanup

**Defined:** 2026-08-01
**Core Value:** Ensure the v5.0 Vault Architecture functions flawlessly in production, legacy data is fully migrated to the new unified state, and UX clearly communicates document properties.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Environment & Testing
 - [ ] **ENV-01**: Add `pylnk3` to `requirements.txt` to fix local test dependencies.
 - [ ] **TEST-01**: Implement an End-to-End test suite targeting the physical `D:\Areas` and `D:\Inbox` directories to validate real-world pipeline execution without mocks.

### Timeline View UX
 - [ ] **TIMELINE-05**: Update timeline numbering so the prefix index represents the starting page of the document (or a cumulative page counter) to implicitly communicate multi-page documents (e.g., `001`, `004` means `001` has 3 pages).

### State Migration Cleanup
 - [ ] **MIGRATE-04**: Update `v5_migration.py` to parse `1_cleaned.json`, `2_grouped.json`, and `3_routed_and_finalized.json`, merge them into a single `state.json` per house, and permanently delete the legacy JSONs from the `.source_files` directory to prevent state conflicts.

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENV-01      | 36    | Mapped |
| TEST-01     | 36    | Mapped |
| TIMELINE-05 | 37    | Mapped |
| MIGRATE-04  | 38    | Mapped |

**Coverage:**
- v1 requirements: 4 total
- Mapped to phases: 4
- Unmapped: 0 ✅

---
*Requirements defined: 2026-08-01*
