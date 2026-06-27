# UAT Test 2 Debug Investigation

## Issue
**User reported:** "no see this is weird, because if you are hitting error 400, that is a credential issue, why are you retrying?"
**Context:** When attempting to test fallback by providing an invalid Gemini key, the system returned a 400 Invalid Argument error. However, instead of immediately failing over to the next provider (OpenRouter), the system retried the request 3 times.

## Root Cause
The fallback logic in `_route_llm_call` within `src/llm.py` checked for auth errors using the following condition:
```python
is_auth = "401" in error_str or "403" in error_str
```
The Gemini API, unlike OpenAI or OpenRouter, often returns a `400 INVALID_ARGUMENT` response when the API key is not valid, or when the model configuration is incorrectly requested. Because "400" was not considered an authentication error by the `is_auth` check, the error fell through to the generic retry block. This caused the system to waste time retrying 3 times with 7.5 seconds sleeps in between before moving on to OpenRouter.

## Resolution
Modified the `is_auth` condition in `src/llm.py` to correctly identify and treat 400 errors as auth/bad-request scenarios that should fail fast:
```python
is_auth = "401" in error_str or "403" in error_str or "400" in error_str or "api key not valid" in error_str or "invalid_api_key" in error_str
```
This ensures that if the Gemini API (or any other provider) returns a 400 bad request error due to credential or model mismatches, the system will immediately fail over to the next available provider, skipping the unnecessary retries.

This resolution successfully addresses the root cause of the UAT Test 2 reported issue, as verified locally using `test_llm_fallback.py`.
