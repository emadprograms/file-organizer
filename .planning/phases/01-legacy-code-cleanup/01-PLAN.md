---
wave: 1
depends_on: []
files_modified: ["src/**"]
autonomous: true
---

# Phase 1: Legacy Code Cleanup - Plan

## Phase Goal
Identify and remove unreachable legacy code within the `src/` folder by tracing imports from the main entry point (`src/organize.py`).

## Requirements
- CLN-01

## must_haves
- All code not reachable from `src/organize.py` (directly or indirectly) must be identified and removed.
- The `tests/` folder must be explicitly ignored for this unused code deletion.
- No active code or functionality must be broken.
- The existing test suite must pass fully after cleanup.
- An end-to-end smoke test on a real PDF must succeed after cleanup.

## Artifacts this phase produces
- No new source code symbols (decorators, classes, functions, CLI flags, struct/dataclass fields) are created in this phase, as it is strictly a cleanup and removal phase.
- `unused_code_report.md`: Artifact file documenting the identified unused code to be removed.

## Tasks

### Wave 1: Discovery

```xml
<task>
  <action>Run static analysis using `vulture` on the `src/` directory and perform manual import tracing from `src/organize.py` using an isolated sub-agent. Document all unused files, classes, and functions in an artifact `unused_code_report.md`.</action>
  <read_first>
    - .planning/phases/01-legacy-code-cleanup/01-CONTEXT.md
    - src/organize.py
  </read_first>
  <acceptance_criteria>
    - `vulture src/` has been executed to gather static analysis signals.
    - A subagent has manually traced imports starting from `src/organize.py` to identify the reachability graph.
    - `unused_code_report.md` artifact is created listing strictly unreachable code in `src/`.
  </acceptance_criteria>
</task>
```

### Wave 2: Deletion

```xml
<task>
  <action>Delete unused files and remove unused functions/classes from `src/` files as listed in the `unused_code_report.md` artifact.</action>
  <read_first>
    - unused_code_report.md
    - src/
  </read_first>
  <acceptance_criteria>
    - All files listed in `unused_code_report.md` as completely unused are deleted.
    - All functions/classes listed in `unused_code_report.md` as unused are removed from their respective files using appropriate file replacement or deletion tools.
    - No code reachable from `src/organize.py` is removed.
  </acceptance_criteria>
</task>
```

### Wave 3: Validation

```xml
<task>
  <action>Run the `pytest` test suite and execute an end-to-end smoke test on a sample PDF using `src/organize.py` to ensure the core workflow is 100% maintained.</action>
  <read_first>
    - src/organize.py
    - tests/
    - .planning/phases/01-legacy-code-cleanup/01-CONTEXT.md
  </read_first>
  <acceptance_criteria>
    - `pytest` executes and all tests pass without errors.
    - `python src/organize.py` successfully processes a test PDF without failing.
  </acceptance_criteria>
</task>
```

## Verification Criteria
- [x] Unreachable code not in the `src/organize.py` dependency graph is removed.
- [x] All test suites pass, verifying no active code was deleted.
- [x] Total codebase size or file count is reduced.
- [x] Core workflow works end-to-end.
