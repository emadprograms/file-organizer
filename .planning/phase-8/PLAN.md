# Phase 8 Plan: Address tech debt: test assertions for logs/fallback

## 1. Upgrade Log Levels in `llm.py`
- **File:** `src/llm/llm.py`
- **Action:** Change `log.info` to `log.warning` for LLM fallback and retry events within `_route_llm_call`. Specifically:
  - "LLM call failed..."
  - "[Cloud Fallback] {provider_name} failed. Failing over to..."
  - "Rate limit hit..." and "Server error..." inside the retry logic.

## 2. Add Caplog Assertions to Fallback Tests
- **File:** `tests/test_fallback_chain.py`
- **Action:** 
  - Inject the `caplog` fixture into `test_mocked_fallback_chain_integration` and `test_live_fallback_invalid_key_fail_fast`.
  - Assert that warnings containing "Cloud Fallback", "failed", or relevant keywords are captured.
  - Set `caplog.set_level(logging.WARNING)` during these tests.

## 3. Add Caplog Assertions to LLM Retry Tests
- **File:** `tests/test_llm.py`
- **Action:** 
  - Identify existing tests that simulate 500 or 429 errors (e.g., if any test mocks an exception that triggers retry in `_route_llm_call`). If there aren't specific unit tests for `_route_llm_call` retries, add one, or use existing `test_pipeline_extended.py` or similar integration test.
  - Inject `caplog` and assert that the expected warnings (like "Rate limit hit, backing off" or "Server error, retrying") are emitted.

## 4. Verify the Test Suite Passes
- **Action:** Run `pytest tests/test_fallback_chain.py tests/test_llm.py` to verify the assertions hold and no log warnings are missed.
