---
wave: 3
depends_on: []
files_modified:
  - tests/test_fallback_chain.py
  - src/llm.py
autonomous: true
---

# Phase 03 Plan: UAT Gap Closure

## Objective
Fix the remaining issues identified in UAT: update `test_route_fails_fast_on_auth_error` to expect fallback behavior instead of an exception, and ensure that if all providers are exhausted, the application handles it gracefully without crashing.

## must_haves
- requirements: CLOUD-02, CLOUD-03, TEST-01
- truths:
  - `tests/test_fallback_chain.py` has a test `test_route_fails_fast_on_auth_error` which expects an `LLMFailureError`. This test needs to be updated to expect the fallback to OpenRouter.
  - `classify_page_direct` currently does not catch exceptions from `_route_llm_call`. If all providers are exhausted, it raises `RuntimeError` and crashes the application. It should catch `RuntimeError` and return a fallback `PageClassification`.
- prohibitions:
  - None

## Tasks

### Task 1: Update Fallback Chain Test
<read_first>
- tests/test_fallback_chain.py
</read_first>
<action>
Update `test_route_fails_fast_on_auth_error` in `tests/test_fallback_chain.py`:
Instead of expecting `pytest.raises(LLMFailureError)`, mock the OpenRouter call just like in `test_route_fallback_immediately_on_500` and assert that `mock_or.assert_called_once()` is true, and `mock_gemini.call_count == 1`.
Rename the test to `test_route_fails_fast_on_auth_error_and_falls_back`.
</action>
<acceptance_criteria>
The test passes and correctly verifies that a 401 error on Gemini immediately triggers a fallback to OpenRouter.
</acceptance_criteria>

### Task 2: Handle Provider Exhaustion Gracefully in classify_page_direct
<read_first>
- src/llm.py
</read_first>
<action>
Modify `classify_page_direct` in `src/llm.py` to catch `RuntimeError` (or any `Exception`) when calling `_route_llm_call`.
If an exception occurs (which means all providers failed), log the error and return a fallback `PageClassification`:
```python
        try:
            result = self._route_llm_call(
                model='gemma-4-26b-a4b-it',
                contents=contents,
                response_schema=PageClassification,
                log_prefix="DirectCloud",
                max_attempts=attempts
            )
            return result
        except Exception as e:
            print(f"[DirectCloud] Error during LLM call: {e}. Returning fallback classification.")
            from src.schemas import Category
            return PageClassification(
                house_number="UNKNOWN",
                residents=[],
                category=Category.MISCELLANEOUS_LETTERS,
                date="NONE",
                summary="Classification failed due to API errors.",
                is_form=False
            )
```
</action>
<acceptance_criteria>
`classify_page_direct` does not crash the application when all providers fail (e.g., due to invalid API keys across all providers).
</acceptance_criteria>
