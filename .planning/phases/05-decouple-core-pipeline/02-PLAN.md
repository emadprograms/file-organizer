---
wave: 1
depends_on: []
files_modified:
  - "src/extractors.py"
  - "tests/test_organizer.py"
  - "tests/test_pipeline.py"
  - "tests/test_pipeline_extended.py"
  - "tests/test_schemas.py"
gap_closure: true
autonomous: true
---

# Phase 05: Decouple Core Pipeline (Gap Closure)

## Goal
Fix `ImportError` exceptions caused by the removal of legacy schema classes (`PageClassification` and `Category`) to enable the test suite and pipeline to execute successfully, closing the verification gaps from Phase 05.

## Requirements
- REF-01: Refactor `src/llm.py` to extract domain-specific prompts.
- REF-02: Refactor `src/organizer.py` to remove hardcoded folder structures and entity parsing.
- REF-03: Refactor `src/pipeline.py` to eliminate hardcoded heuristic strategies.

## Tasks

### Wave 1: Core Code Fixes

<task>
<read_first>
- src/extractors.py
- src/schemas.py
</read_first>
<action>
1. Remove all import statements referencing `PageClassification` and `Category` from `src/extractors.py` (e.g. `from src.schemas import PageClassification, Category`).
2. Refactor any type hints, function signatures, and method bodies in `src/extractors.py` that reference `PageClassification` or `Category`. Replace them with standard `dict` or dynamically resolved schema types based on the new configuration-driven design.
3. Update any internal instantiations of `PageClassification` to instead return a `dict` with string keys that match the configured schema.
</action>
<acceptance_criteria>
- `grep "PageClassification" src/extractors.py` returns no results.
- `grep "Category" src/extractors.py` returns no import results.
- Running `python -c "import src.extractors"` exits with code 0.
</acceptance_criteria>
</task>

### Wave 2: Test Suite Fixes

<task>
<read_first>
- tests/test_organizer.py
- tests/test_pipeline.py
- tests/test_pipeline_extended.py
- tests/test_schemas.py
- src/llm.py
- src/pipeline.py
</read_first>
<action>
1. Search and remove all imports of `PageClassification` and `Category` from `tests/test_organizer.py`, `tests/test_pipeline.py`, `tests/test_pipeline_extended.py`, `tests/test_schemas.py`, and any scripts in the `scratch/` directory.
2. Refactor test setups and mocks to replace `PageClassification(...)` instantiations with mocked dictionaries or dynamic models built via Pydantic's `create_model`, matching the new expectations of `src/pipeline.py`.
3. Provide mocked or dummy `UserConfig` configuration contexts where necessary to satisfy tests now relying on config rather than hardcoded enums.
4. Remove or update test cases in `tests/test_schemas.py` that explicitly tested the `Category` enum or `PageClassification` static model.
</action>
<acceptance_criteria>
- `python -m pytest --collect-only tests/` executes successfully without `ImportError`.
- `grep -r "from src.schemas import .*PageClassification" tests/` returns no results.
- `grep -r "from src.schemas import .*Category" tests/` returns no results.
- Running `python -m pytest tests/` does not fail due to schema import errors.
</acceptance_criteria>
</task>

## Artifacts this phase produces
- Modified `src/extractors.py` using dynamic types and dictionaries.
- Updated test suite files (`tests/test_organizer.py`, `tests/test_pipeline.py`, `tests/test_pipeline_extended.py`, `tests/test_schemas.py`).
- Updated `scratch` scripts (if affected).

## Verification Criteria
- The pytest collection phase completes successfully without `ImportError`.
- No references to `PageClassification` or `Category` from `src.schemas` exist in `src/` or `tests/`.

## Must Haves

<must_haves>
  <truths>
    - `src/extractors.py` successfully loads without importing `PageClassification` or `Category`.
    - The test suite in `tests/` executes without collection errors or `ImportError`.
    - Test fixtures utilize dynamic schemas or dictionaries instead of legacy hardcoded BaseModels.
  </truths>
  <prohibitions>
    - No file in `src/` or `tests/` MUST import `PageClassification` from `src.schemas`.
    - No file in `src/` or `tests/` MUST import `Category` from `src.schemas`.
  </prohibitions>
</must_haves>
