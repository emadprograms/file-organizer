---
wave: 1
depends_on: []
files_modified:
  - src/pipeline.py
  - src/llm.py
  - src/organizer.py
  - src/config.py
  - src/schemas.py
  - src/ingest.py
  - src/split.py
  - src/main.py
  - tests/test_pipeline.py
  - tests/test_llm.py
  - tests/test_e2e.py
autonomous: true
---

# Phase 04 Plan: Audit & Fix

## Goal
Audit code for bugs and fix them, establishing a clean and stable foundation.

## Requirements
- TEST-02

## Tasks

### Wave 1

<task>
<read_first>
- src/pipeline.py
- src/llm.py
- src/config.py
</read_first>
<action>
Consolidate refactoring for pipeline.py and llm.py to prevent concurrent modifications:
- Error Handling: Delete `_get_fallback_house_number` in `src/pipeline.py`. Remove the `try...except` block around the classification call (e.g., `self.client.classify_page_direct` or equivalent) that catches exceptions and generates a dummy `PageClassification` fallback. Allow exceptions like `RuntimeError` from the LLM provider cascade in `src/llm.py` to bubble up unhandled, so the application crashes immediately on failure.
- Logging: Replace all `print()` calls in `src/pipeline.py` and `src/llm.py` with appropriate standard `logging` calls. Completely remove the `try: print(msg) except UnicodeEncodeError:` pattern in `src/pipeline.py`.
- Type Hinting & Cleanup: Update type hinting to use built-in generic types (`list[str]`, `dict[str, Any]`, `tuple`) instead of `typing.List`, `typing.Dict`, `typing.Tuple` across both files. Clean up unused imports.
</action>
<acceptance_criteria>
- `src/pipeline.py` does not contain the string `_get_fallback_house_number`.
- `src/pipeline.py` no longer contains a `try...except` block that generates dummy `PageClassification` fallbacks for classification errors.
- `src/pipeline.py` does not contain the string `except UnicodeEncodeError:`.
- `src/pipeline.py` and `src/llm.py` import and use `logging` or a `logger` instance instead of `print()`.
- No `from typing import List`, `Dict`, or `Tuple` statements exist in `src/pipeline.py` or `src/llm.py`.
</acceptance_criteria>
</task>

<task>
<read_first>
- src/organizer.py
- src/schemas.py
- src/ingest.py
- src/split.py
- src/config.py
- src/main.py
</read_first>
<action>
Consolidate refactoring for the remaining codebase:
- In `src/config.py`, implement a `setup_logging()` function that configures a central logger for the application.
- In `src/organizer.py`, replace all `print()` calls with appropriate `logging` calls.
- In `src/organizer.py`, refactor `_normalize_date` by extracting its complex datetime parsing logic into a new helper function `_parse_datetime_str` to improve readability.
- Update type hinting to use built-in generic types (`list[str]`, `dict[str, Any]`, `tuple`) instead of `typing.List`, `typing.Dict`, `typing.Tuple` across `src/organizer.py`, `src/schemas.py`, `src/ingest.py`, `src/split.py`, `src/config.py`, and `src/main.py`.
- Clean up unused imports in these files.
</action>
<acceptance_criteria>
- `src/config.py` contains `def setup_logging(`.
- `src/organizer.py` contains `def _parse_datetime_str(`.
- `src/organizer.py` imports and uses `logging` or a `logger` instance instead of `print()`.
- No `from typing import List`, `Dict`, or `Tuple` statements exist in these updated files.
</acceptance_criteria>
</task>

### Wave 2

<task>
<read_first>
- src/pipeline.py
- src/llm.py
</read_first>
<action>
Implement unit tests to verify fail-fast behavior.
- Create `tests/test_pipeline.py` with mock tests to simulate exceptions in the classification pipeline. Assert that it raises the exception instead of generating a fallback.
- Create `tests/test_llm.py` with mock tests to simulate API exhaustion. Assert that it correctly throws a `RuntimeError`.
</action>
<acceptance_criteria>
- `tests/test_pipeline.py` contains tests that mock classification exceptions and assert the exception is raised.
- `tests/test_llm.py` contains tests that mock API exhaustion and assert `RuntimeError` is raised.
- `pytest tests/test_pipeline.py tests/test_llm.py` executes successfully and passes all mock tests.
- `mypy src/` passes without type errors.
</acceptance_criteria>
</task>

<task>
<read_first>
- src/main.py
</read_first>
<action>
Implement and run End-to-End Output Consistency validation as required by Phase 04 Research.
- Create an end-to-end test script `tests/test_e2e.py` (or a shell script) that runs the pipeline against a known sample PDF.
- The test must verify that the logging output is properly encoded (no Unicode errors).
- The test must verify that the output document groupings match expected results exactly as they did before the refactor, ensuring no regressions.
</action>
<acceptance_criteria>
- `tests/test_e2e.py` exists and executes the pipeline on a sample PDF.
- Running the end-to-end test successfully verifies output grouping matches expected results without any Unicode errors.
</acceptance_criteria>
</task>

## Verification

<must_haves>
  <truths>
    - The pipeline fails fast immediately when the LLM client exhausts options and raises a `RuntimeError`.
    - All telemetry uses standard `logging`, and no encoding-related `print` crash-handlers exist.
    - `src/` uses modern built-in type hints (`list`, `dict`) consistently instead of `typing` module equivalents.
    - `pytest tests/` successfully runs the mock unit tests for API exhaustion and fail-fast behavior.
    - End-to-End Output Consistency validation passes on a sample PDF without regressions or Unicode errors.
    - Static analysis (e.g. `mypy src/`) passes smoothly.
  </truths>
  <prohibitions>
    - statement: The application must not swallow classification exceptions with dummy fallbacks.
      status: resolved
      verification: `src/pipeline.py` does not contain `_get_fallback_house_number`.
  </prohibitions>
</must_haves>

## Artifacts this phase produces
- `setup_logging` function in `src/config.py`
- `_parse_datetime_str` function in `src/organizer.py`
- `tests/test_pipeline.py` file
- `tests/test_llm.py` file
- `tests/test_e2e.py` file
