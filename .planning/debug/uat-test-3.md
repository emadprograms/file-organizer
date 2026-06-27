# UAT Test 3 Debug

## Issue
When both Gemini and OpenRouter fail due to invalid keys, the system should automatically fall back to Groq. Instead, the user reported: "Same root cause as Test 2. The 401 error raised an exception instead of failing over to Groq."

## Root Cause
The root cause was that `src/llm.py`'s `_route_llm_call` was explicitly coded to `raise LLMFailureError` upon detecting an authentication error (like a 401 from OpenRouter). When OpenRouter failed with a 401 error, instead of gracefully incrementing `current_provider_idx` and continuing to Groq, the system raised an `LLMFailureError` exception and crashed the request.

This issue applied to both Test 3 (raising an exception instead of falling back to Groq) and Test 5 (system crashes instead of failing over).

## Fix Status
The exception-raising behavior has already been fixed in a recent commit (replaced `raise LLMFailureError` with `continue` logic to proceed to the next provider).

Additionally, local unstaged changes currently add `400` to the `is_auth` check to properly catch Gemini's `400 INVALID_ARGUMENT` authentication errors, which addresses the root cause of Test 2.

**Note:** The unit test `test_route_fails_fast_on_auth_error` in `tests/test_fallback_chain.py` expects the system to raise `LLMFailureError` and will currently fail because the system now correctly falls back to the next provider. This unit test needs to be updated to expect a fallback instead of an exception.
