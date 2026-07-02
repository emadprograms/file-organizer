# Testing

**Focus:** quality
**Date:** 2026-07-01

## Framework
- **Pytest**: The primary test framework used. Found in `requirements.txt` and verified via test file naming conventions.

## Structure
- Tests are located in the `/tests` directory.
- `conftest.py` is present, suggesting the use of shared fixtures.
- Unit tests are mapped directly to modules (`test_ingest.py`, `test_llm.py`, `test_pipeline.py`, `test_organizer.py`, `test_split.py`, `test_schemas.py`).
- Contains `test_e2e.py` for end-to-end testing of the entire document processing flow.
- Contains `test_providers.py` and `test_fallback_chain.py` for testing LLM provider fallback logic.

## Mocking & Strategies
- External APIs (like Gemini/OpenAI) are likely mocked in unit tests, though this isn't strictly viewable without inspecting `conftest.py`.
- The presence of `test_e2e.py` indicates testing spans both mocked units and full integrations (potentially with real or dummy PDFs).
