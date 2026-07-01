---
phase: 03-organization-logic-grouping-routing
plan: 01
subsystem: core
tags: [pipeline, grouping, routing]

# Dependency graph
requires:
  - phase: 02-extraction-and-cleaning-logic
    provides: [config-driven Pass 1 and 1.5]
provides:
  - Config-driven grouping and routing
  - Sample python scripts for grouping and routing
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [python-script-injection, declarative-grouping, template-routing]

key-files:
  created: [scripts/sample-grouping.py, scripts/sample-routing.py]
  modified: [src/schemas.py, sample-config.yaml, tests/test_schemas.py, src/pipeline.py, src/organizer.py, src/main.py, tests/test_organizer.py]

key-decisions:
  - "Extracted logic to Python scripts to allow for custom pipeline execution while maintaining existing system behavior"
  - "Added declarative grouping by fields"
  - "Implemented template-based routing with a fallback folder"

patterns-established:
  - "Pattern 1: Python script injection for grouping and routing"
  - "Pattern 2: String formatting based routing templates"

requirements-completed: []

coverage:
  - id: D1
    description: "ConfigGrouping model added and used for declarative and python grouping in pipeline"
    verification:
      - kind: unit
        ref: "tests/test_pipeline.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "ConfigRouting model added and used for template and python routing in organizer"
    verification:
      - kind: unit
        ref: "tests/test_organizer.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "Sample configuration explicitly points to sample-grouping.py and sample-routing.py"
    verification:
      - kind: unit
        ref: "tests/test_schemas.py"
        status: pass
    human_judgment: false

# Metrics
duration: 8 min
completed: 2026-07-01
status: complete
---

# Phase 3 Plan 01: Organization Logic Summary

**Replaced hardcoded grouping and routing logic with config-driven dynamic grouping, routing templates, and external Python script injection.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-07-01T18:41:45Z
- **Completed:** 2026-07-01T18:48:30Z
- **Tasks:** 5
- **Files modified:** 9

## Accomplishments
- Configurable grouping using a declarative or python script strategy.
- Configurable routing using a template format or python script strategy.
- Extraction of original complex algorithms to `sample-grouping.py` and `sample-routing.py`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add config schemas** - `fe0ca56` (feat)
2. **Task 2: Extract Pass 2 logic** - `9cf6fa3` (feat)
3. **Task 3: Extract Pass 3 logic** - `8e4d48b` (feat)
4. **Task 4: Refactor Pass 2** - `fa1fad6` (feat)
5. **Task 5: Refactor Pass 3** - `2108cdb` (feat)

**Plan metadata:** TBD

## Files Created/Modified
- `src/schemas.py` - Added ConfigGrouping and ConfigRouting
- `sample-config.yaml` - Updated with new strategy settings
- `tests/test_schemas.py` - Added assertions for new config fields
- `scripts/sample-grouping.py` - Extracted boundary and bulk logic
- `scripts/sample-routing.py` - Extracted organizer and pdf generation logic
- `src/pipeline.py` - Refactored `_group_pages_into_documents`
- `src/organizer.py` - Refactored `organize`
- `src/main.py` - Piped UserConfig
- `tests/test_organizer.py` - Updated to use mock `UserConfig`

## Decisions Made
- Extracted logic to Python scripts to allow for custom pipeline execution while maintaining existing system behavior.
- Added declarative grouping by fields.
- Implemented template-based routing with a fallback folder.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
Phase complete, ready for next step.

## Self-Check: PASSED
