---
phase: 04-output-structure-reconciliation
plan: 01
subsystem: file-system
tags: [reconciliation, filesystem, pydantic]

# Dependency graph
requires:
  - phase: 03-pass-2-grouping
    provides: [Split DocumentGroups ready for physical writing]
provides:
  - Rewritten FileOrganizer that creates physical directories (house/tenant timeline/topic) on demand
  - run_reconciliation logic to assert total pages input vs output and write the manifest
affects: [05-dry-run]

# Tech tracking
tech-stack:
  added: []
  patterns: [Atomic file writing with temp replacements]

key-files:
  created: []
  modified:
    - src/processing/organizer.py
    - tests/test_organizer.py

key-decisions:
  - "Decided to keep organizer.organize focused on building the directory tree and writing segments, returning only a mapping of pages to locations."
  - "Reconciliation logic explicitly raises RuntimeError if total_input_pages != total_output_pages."
  - "Tenant timelines computed via a global pre-aggregation pass across all grouped documents."

patterns-established:
  - "Pattern 1: On-demand directory creation — folders are only created when a document actually routes to them."

requirements-completed: [OUT-01, OUT-02, OUT-03, OUT-04, OUT-05, OUT-06, LOG-04, DIFF-03]

coverage:
  - id: D1
    description: "Rewrite FileOrganizer core & routing to support timeline aggregation and on-demand topics"
    requirement: "OUT-02"
    verification:
      - kind: unit
        ref: "pytest tests/test_organizer.py::test_tenant_directories_timeline"
        status: pass
    human_judgment: false
  - id: D2
    description: "Implement Unassigned edge case fallback logic"
    requirement: "OUT-05"
    verification:
      - kind: unit
        ref: "pytest tests/test_organizer.py::test_unassigned_folder_fallback"
        status: pass
    human_judgment: false
  - id: D3
    description: "Implement run_reconciliation logic and assert input equals output"
    requirement: "OUT-06"
    verification:
      - kind: unit
        ref: "pytest tests/test_organizer.py::test_page_count_reconciliation"
        status: pass
    human_judgment: false
  - id: D4
    description: "Write reconciliation manifest JSON output"
    requirement: "DIFF-03"
    verification:
      - kind: unit
        ref: "pytest tests/test_organizer.py::test_reconciliation_manifest"
        status: pass
    human_judgment: false

# Metrics
duration: 4min
completed: 2026-07-05T04:38:00Z
status: complete
---

# Phase 04 Plan 01: File Organizer & Reconciliation Summary

**Rewrote FileOrganizer to support tenant timelines and dynamic topic subdirectories, and implemented strict page-count reconciliation check.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-05T04:34:20Z
- **Completed:** 2026-07-05T04:38:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- FileOrganizer now computes the `min_year` and `max_year` across all grouped documents for each primary tenant and creates timeline-suffixed directories.
- Unassigned tenant dynamically infers `غير محدد {year_start}-{year_end}/` or falls back to just `غير محدد/` when no dates are available.
- Topic subdirectories are created strictly on demand.
- Implemented `run_reconciliation` function that writes a complete JSON manifest and raises a `RuntimeError` if output pages do not equal input pages.

## Task Commits

Each task was committed atomically:

1. **Task 1 & 2: FileOrganizer & Reconciliation** - `1aa3d80` (feat)

## Files Created/Modified
- `src/processing/organizer.py` - Rewrote FileOrganizer and added run_reconciliation logic
- `tests/test_organizer.py` - Rebuilt test suite to validate the new structural logic and reconciliation function

## Decisions Made
- Recomputed `tenant_years` in a single pass to ensure accurate timelines for each tenant, including the 'Unassigned' fallback logic handling.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- The `defaultdict(set)` behavior for `tenant_years` did not populate a key if a tenant only had `NONE` dates, which broke the `test_unassigned_folder_fallback`. Resolved by explicitly instantiating the key for every document before looping over its dates.

## Next Phase Readiness
Ready for Pipeline Integration (04-02).
