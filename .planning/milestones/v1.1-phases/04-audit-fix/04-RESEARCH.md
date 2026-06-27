# Phase 04 Research: Audit & Fix

## 1. Current State Assessment
Based on an audit of the current codebase (`src/pipeline.py`, `src/llm.py`, `src/organizer.py`, `src/schemas.py`, and `src/ingest.py`), the following areas need addressing to align with the Phase 4 goals of structural cleanliness and failing fast:

### 1.1 Error Handling & "Fail Fast" Compliance
- **Current Issue**: `pipeline.py` swallows exceptions during cloud classification (`self.client.classify_page_direct`). Instead of failing, it generates a dummy `PageClassification` fallback using `_get_fallback_house_number`.
- **Required Fix**: Remove `_get_fallback_house_number` and the fallback `try...except` block in `pipeline.py`. If the LLM provider cascade in `llm.py` exhausts all options and throws a `RuntimeError`, `pipeline.py` must crash immediately to prevent bad state propagation. 

### 1.2 Code Smells & Logging
- **Current Issue**: The codebase relies heavily on raw `print()` statements for telemetry. In `pipeline.py`, there is a repetitive and messy `try: print(msg) except UnicodeEncodeError:` pattern to handle console encoding issues.
- **Required Fix**: Replace all `print()` calls with Python's standard `logging` module. Configure a central logger that gracefully handles UTF-8 encoding.

### 1.3 Type Hinting & Structural Cleanliness
- **Current Issue**: Mixed usage of generic types (`List`, `Dict`, `Tuple` from `typing`) and built-in generic types (`list`, `dict`, `tuple`). 
- **Required Fix**: Standardize type hinting across all files to use built-in generics (e.g., `list[str]`, `dict[str, Any]`) as supported by modern Python, ensuring `mypy` or `pyright` compliance.
- **Current Issue**: `organizer.py` contains monolithic functions (like `_normalize_date`) that could be simplified or better structured.
- **Required Fix**: Clean up regex logic and extract complex datetime parsing into helper functions to improve readability.

## 2. Planning Considerations
To plan this phase effectively, the following tasks must be included in `PLAN.md`:
1. **Refactor Logging**: Introduce a `setup_logging()` utility in `main.py` or `config.py` and replace `print` statements in `pipeline.py`, `llm.py`, and `organizer.py`.
2. **Enforce Fail Fast**: Strip out the fallback response logic in `pipeline.py`'s Pass 1. Ensure `RuntimeError` from `llm.py` bubbles up and halts the application.
3. **Type Hinting Standardization**: Perform a sweep across `src/` to unify type hinting syntax.
4. **Code Cleanup**: Remove dead code (`_get_fallback_house_number` in `pipeline.py`, unused imports).

## Validation Architecture

To ensure the fixes meet the criteria of TEST-02 and establish a stable foundation, the validation architecture for Phase 4 will consist of:

1. **Static Analysis & Linting**:
   - Run `mypy` to enforce strict type checking across the newly standardized type hints.
   - Use `ruff` or `flake8` to detect unused imports and code smells.

2. **Fail Fast Verification (Unit Testing)**:
   - Introduce mock tests for `llm.py` and `pipeline.py` to simulate API exhaustion.
   - Assert that `pipeline.py` raises a fatal exception instead of silently returning a fallback `PageClassification`.

3. **End-to-End Output Consistency**:
   - Run the pipeline against a known sample PDF.
   - Verify that the logging output is properly encoded (no Unicode errors) and that the output document groupings match expected results exactly as they did before the refactor, ensuring no regressions.
