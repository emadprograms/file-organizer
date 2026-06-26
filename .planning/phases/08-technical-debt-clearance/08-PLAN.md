---
wave: 1
depends_on: []
files_modified:
  - src/llm.py
  - src/organizer.py
  - tests/test_llm.py
  - tests/test_organizer.py
autonomous: true
---

# Phase 08: Technical Debt Clearance & Code Hardening

## Context & Goal
Perform a comprehensive audit of the codebase to identify and remove dead code, orphaned logic, and redundant functions resulting from multiple iterations in Phase 7. Harden the remaining core logic to ensure stability and maintainability by applying strict type safety, validation at key data boundaries, and updating documentation.

## Tasks

<task>
<read_first>
- src/llm.py
- src/organizer.py
</read_first>
<action>
Execute a dead code audit and logic consolidation.

1. Use automated tools (e.g. `vulture` or similar analysis) to identify unused helper functions, legacy API call paths, and commented-out code blocks in `src/llm.py` and `src/organizer.py`.
2. Remove all identified dead code.
3. Consolidate redundant logic paths in both files (especially leftovers from earlier vision-to-text iterations) into clean, single-purpose abstractions.
4. Ensure test coverage is maintained or increased for the consolidated logic.
</action>
<acceptance_criteria>
- All unused functions and commented-out code are removed.
- Redundant logic paths are consolidated.
- Running the full test suite exits 0 without regressions.
</acceptance_criteria>
</task>

<task>
<read_first>
- src/llm.py
- src/organizer.py
- src/schemas.py
</read_first>
<action>
Implement Type Safety and Validation Hardening.

1. Ensure type hints are consistently applied across `src/llm.py` and `src/organizer.py`.
2. Add strict validation using Pydantic (or the existing validation library) to key data boundaries, especially when parsing LLM JSON responses.
3. Use a static type checker like `mypy` to enforce the new type hints.
</action>
<acceptance_criteria>
- Type hints cover all consolidated and existing functions in `llm.py` and `organizer.py`.
- Strict validation is enforced at LLM output boundaries.
- Running `mypy src/` passes with no type errors.
</acceptance_criteria>
</task>

<task>
<read_first>
- src/llm.py
- src/organizer.py
</read_first>
<action>
Documentation & Schema Sync.

1. Update docstrings for all modified and consolidated functions in `src/llm.py` and `src/organizer.py` to accurately reflect their new single-purpose nature.
2. Ensure project architecture documentation and schemas reflect the new consolidated flow.
</action>
<acceptance_criteria>
- All updated core functions have accurate docstrings.
- High-level architecture docs reflect the current implementation.
</acceptance_criteria>
</task>

## Verification

### must_haves

```yaml
must_haves:
  truths:
    - statement: "CLEAN-01: Dead code and orphaned logic are removed"
      verification: "src/llm.py and src/organizer.py contain no commented-out logic or unused legacy code paths"
    - statement: "CLEAN-02: Logic paths are consolidated"
      verification: "Vision-to-text and classification routines are streamlined in src/llm.py"
    - statement: "CLEAN-03: Type safety and validation are hardened"
      verification: "Pydantic validation and type hints are applied, and mypy passes"
    - statement: "CLEAN-04: Documentation is synced"
      verification: "Docstrings are updated for modified functions"
    - statement: "No regressions"
      verification: "The full test suite passes"
  prohibitions: []
```

## Artifacts this phase produces
- Cleaned and consolidated `src/llm.py`
- Cleaned and consolidated `src/organizer.py`
- Updated docstrings and type hints
