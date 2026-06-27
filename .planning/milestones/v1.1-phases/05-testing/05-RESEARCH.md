# Phase 5: Testing - Research

**Objective:** What do I need to know to PLAN this phase well?

## 1. Scope & Requirements
- **Goal:** Add comprehensive unit and integration tests (Requirement: `TEST-01`), ensuring code hardening.
- **Out of Scope for now:** Automated CI setup (e.g., GitHub Actions), strict test coverage thresholds, and local model testing (local model logic was removed in Phase 01).

## 2. Key Areas to Test
- **Fallback Chain (Integration Tests):** 
  - Ensure routing behaves correctly across the Gemini -> OpenRouter -> Groq chain.
  - As per Decision `D-02`, you must test this by hitting the actual APIs with dummy/invalid API keys to trigger actual errors and validate fallback routing and error handling.
  - Critical integration points: `src/pipeline.py` (engine orchestration) and `src/llm.py` (API wrappers/routing).
- **Core Logic (Unit Tests):**
  - Verify structured output parsing using the Pydantic `BaseModel`.
  - Validate custom error handling and exceptions, particularly `LLMFailureError` and `InvalidResponseError`.
  - Ensure the two-pass categorization engine (`pipeline.py`) and file output structuring (`organizer.py`) behave as expected, considering the recent Phase 04.1 refactoring.

## 3. Testing Strategy & Implementation Guidelines
- **Framework & Location:** Use `pytest` for all tests (already configured). Place new automated tests in the `tests/` directory.
- **Caching / Record-Replay (Decision D-01):**
  - Leverage the existing `.cache.json` and pipeline caching logic to test integration scenarios without repeatedly hitting external endpoints. 
  - This mechanism allows for a record/replay approach for reliable and repeatable LLM test execution.
- **Mocking vs Actual Network:** 
  - Combine standard mocking (`unittest.mock.patch`) for unit tests with live network calls using invalid keys for testing the fallback chain directly.

## 4. Existing Test Environment Status
- `pytest` is already established in the repository. 
- Some basic placeholder or minimal tests already exist (e.g., `tests/test_llm.py`, `tests/test_pipeline.py`).
- There is a completely empty test file (`tests/test_fallback_chain.py`) ready to be populated.
- `scripts/` contains older manual evaluation tools (like `evaluate_local.py`), which are separate from the automated `pytest` suite being built in this phase.
