---
status: diagnosed
phase: 03-cloud-fallback
source: 03-SUMMARY.md
started: 2026-06-27T19:23:05+03:00
updated: 2026-06-27T20:11:00+03:00
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 5
name: Fail Fast on Auth Errors
expected: |
  If a provider returns a 401 or 403 authorization error (e.g., due to an invalid key), the system immediately fails over to the next provider without attempting to retry.
awaiting: user response

## Tests

### 1. Normal Gemini Request
expected: The application categorizes a file correctly using the primary Gemini provider when API keys are valid, returning valid JSON without invoking fallbacks.
result: pass

### 2. Fallback to OpenRouter
expected: When the Gemini API fails (e.g. due to simulated 5xx or invalid Gemini key but valid OpenRouter key), the system automatically falls back to OpenRouter. The request succeeds and returns valid JSON.
result: issue
reported: "no see this is weird, because if you are hitting error 400, that is a credential issue, why are you retrying?"
severity: major

### 3. Fallback to Groq
expected: When both Gemini and OpenRouter fail (e.g. due to invalid keys), the system automatically falls back to Groq. The request succeeds and returns valid JSON.
result: issue
reported: "run it and check for groq. give wrong gemini and operouter key and check."
severity: major

### 4. 429 Rate Limit Retry
expected: When the active provider returns a 429 Rate Limit error, the system pauses for approximately 65 seconds and retries the request with the same provider before failing over.
result: pass

### 5. Fail Fast on Auth Errors
expected: If a provider returns a 401 or 403 authorization error (e.g., due to an invalid key), the system immediately fails over to the next provider without attempting to retry.
result: issue
reported: "fail."
severity: major

## Summary

total: 5
passed: 2
issues: 3
pending: 0
skipped: 0

## Gaps

- truth: "When the Gemini API fails (e.g. due to simulated 5xx or invalid Gemini key but valid OpenRouter key), the system automatically falls back to OpenRouter. The request succeeds and returns valid JSON."
  status: failed
  reason: "User reported: no see this is weird, because if you are hitting error 400, that is a credential issue, why are you retrying?"
  severity: major
  test: 2
  root_cause: "Gemini invalid key returns 400 INVALID_ARGUMENT instead of 401/403, causing the error to bypass the auth failure check and retry instead of failing over."
  artifacts:
    - path: "src/llm.py"
      issue: "is_auth check doesn't include '400' or 'invalid_api_key'"
  missing:
    - "Add '400' and 'invalid_api_key' to is_auth check in _route_llm_call"
  debug_session: ".planning/debug/uat-test-2.md"

- truth: "When both Gemini and OpenRouter fail (e.g. due to invalid keys), the system automatically falls back to Groq. The request succeeds and returns valid JSON."
  status: failed
  reason: "User reported: Same root cause as Test 2. The 401 error raised an exception instead of failing over to Groq."
  severity: major
  test: 3
  root_cause: "_route_llm_call explicitly raised LLMFailureError on auth error instead of continuing to the next provider. (Fixed in recent commit, but tests need updating)"
  artifacts:
    - path: "src/llm.py"
      issue: "raise LLMFailureError instead of continue (already fixed in recent commit)"
    - path: "tests/test_fallback_chain.py"
      issue: "test_route_fails_fast_on_auth_error expects LLMFailureError"
  missing:
    - "Update test_route_fails_fast_on_auth_error to expect fallback behavior"
  debug_session: ".planning/debug/uat-test-3.md"

- truth: "The application requires all 3 API keys to start, and hardcodes the provider list to always check Gemini, OpenRouter, and Groq."
  status: failed
  reason: "User requested enhancement: Make OpenRouter and Groq optional. Fallback logic should dynamically skip providers that do not have an API key configured, instead of crashing or wasting time retrying."
  severity: minor
  test: 4
  root_cause: "load_config strictly required all keys and crashed; _route_llm_call had a hardcoded providers list. (Fixed in commit c0561b97)"
  artifacts:
    - path: "src/config.py"
      issue: "Required OPENROUTER_API_KEY and GROQ_API_KEY (Fixed)"
    - path: "src/llm.py"
      issue: "Hardcoded providers list (Fixed)"
  missing: []
  debug_session: ".planning/debug/uat-test-4.md"

- truth: "If a provider returns a 401 or 403 authorization error (e.g., due to an invalid key), the system immediately fails over to the next provider without attempting to retry."
  status: failed
  reason: "User reported: fail. The system crashes instead of failing over."
  severity: major
  test: 5
  root_cause: "When all providers exhausted, RuntimeError is thrown. check_bulk_semantic_grouping explicitly re-raised it instead of returning fallback data gracefully."
  artifacts:
    - path: "src/llm.py"
      issue: "check_bulk_semantic_grouping re-raises RuntimeError on exhaustion"
  missing:
    - "Catch RuntimeError in check_bulk_semantic_grouping and return BulkSemanticMatchResult fallback"
  debug_session: ".planning/debug/uat-test-5.md"
