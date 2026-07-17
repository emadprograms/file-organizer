# Summary: Wave 1 - Standardize Loggers

## Objective
Migrate all logger instantiations in the codebase to a strict hierarchical pattern and standardize the logger variable name to `logger`.

## Changes
- **Source Code (`src/`)**: 
    - Updated all module-level logger instantiations to use `logger = logging.getLogger(f"file_organizer.{__name__}")`.
    - Standardized variable names from `log` or other variants to `logger` across all modules.
    - Modules updated include:
        - `src/cleaning/phase.py`
        - `src/cleaning/tenants.py`
        - `src/llm/llm.py`
        - `src/llm/providers.py`
        - `src/organize.py`
        - `src/processing/grouping/core.py`
        - `src/processing/organizer/core.py`
        - `src/processing/organizer/reconciliation.py`
        - `src/processing/pdf/compress.py`
        - `src/processing/pipeline.py`
        - `src/processing/routing/router.py`
    - `src/logger.py` was correctly excluded as it manages the root and base logger configuration.

- **Tests (`tests/`)**:
    - Reviewed `tests/` directory. Existing `getLogger` calls in `tests/test_logger.py` and `tests/verify_dual_logging.py` were identified as necessary for testing the logging framework itself and were preserved.

## Verification
- Verified via `grep_search` that all target modules in `src/` now use the `file_organizer.{__name__}` pattern.
- Confirmed no legacy `logging.getLogger(__name__)` or non-standard logger variable names remain in the source.

## Outcome
The codebase now follows a consistent, hierarchical logging structure, enabling precise log filtering and alignment with the project's logging requirements.
