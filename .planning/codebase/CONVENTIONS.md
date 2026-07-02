# Conventions

**Focus:** quality
**Date:** 2026-07-01

## Code Style & Patterns
- **Typing**: Type hints are heavily used (e.g., `list[tuple[int, PageClassification]]`, `Optional[Any]`).
- **Data Validation**: Pydantic is used for structured data models in `schemas.py`.
- **Modularity**: Code is split into focused modules (ingest, llm, pipeline, organizer, extractors, split).
- **Logging**: Python's standard `logging` library is used extensively to track pipeline progression (e.g., `logger.info(f"Starting Pass 1...")`).

## Error Handling
- Custom exceptions are used to signal specific failure states (e.g., `LLMFailureError`, `InvalidResponseError` in `llm.py`).
- Tenacity is employed for retry logic on flaky API calls (configured in `llm.py` or `providers.py`).
- Defensive checks exist to abort processing gracefully rather than losing data (e.g., throwing `RuntimeError` if page loss is detected during extraction).

## Naming
- Python standards apply (snake_case for variables/functions, PascalCase for classes).
- Specific module files prefix tests with `test_` for pytest compatibility.
