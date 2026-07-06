# Phase 8 Research: Log/Fallback Test Assertions

## Current State

The test suite (`test_fallback_chain.py` and `test_llm.py`) verifies that the LLM client correctly retries or falls back to secondary providers when encountering specific errors (e.g., 503 Service Unavailable, 500 Internal Error, or invalid keys). 

However, the tests lack assertions that ensure appropriate logging is occurring during these events. While `mock_gemini.call_count` is checked, there is no validation that the user or pipeline operator is being notified through logs about these degradations or retries. A grep for `caplog` yields no results in `test_llm.py` or `test_fallback_chain.py`.

## Tech Debt Identified

1. **Retry Logging Not Asserts**: When `tenacity` retries an LLM call due to a 50x or 429 error, a warning or info log should be emitted. The tests do not verify this log output.
2. **Fallback Logging Not Asserted**: When `LLMClient._route_llm_call` catches an exception after max retries and falls back to a secondary provider (e.g., OpenRouter or Groq), a warning log should be emitted. Currently, `test_mocked_fallback_chain_integration` only asserts that the mock functions are called, not that the fallback warning was printed.
3. **No `caplog` Usage**: The `pytest` standard fixture `caplog` is currently unutilized in these files.

## Recommended Implementation Plan

1. **Update `test_fallback_chain.py`**:
   - Inject `caplog` fixture into `test_mocked_fallback_chain_integration`.
   - Add assertions to ensure `WARNING` level logs are captured containing keywords like "Fallback" or "provider".
   - Inject `caplog` fixture into `test_live_fallback_invalid_key_fail_fast`.
   - Add assertions to verify that invalid keys generate expected error logs.

2. **Update `test_llm.py`**:
   - Add `caplog` to relevant tests involving 500/429 retries (e.g., `test_generate_json_retry_on_500`, `test_generate_json_retry_on_429`).
   - Add assertions that `tenacity`'s retry logs (or custom before_sleep hooks) emit warnings. (If custom logging for tenacity isn't set up, we should add it using `tenacity.before_sleep_log`).

3. **Modify Code if Necessary**:
   - Ensure `src/llm/llm.py` actually emits clear, testable log lines when falling back or retrying, using `logger.warning` or `logger.error`. 

This closes the tech debt and ensures operational observability during degraded LLM API performance.
