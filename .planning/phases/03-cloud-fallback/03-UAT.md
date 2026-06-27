---
status: failed
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
  artifacts: []
  missing: []

- truth: "When both Gemini and OpenRouter fail (e.g. due to invalid keys), the system automatically falls back to Groq. The request succeeds and returns valid JSON."
  status: failed
  reason: "User reported: Same root cause as Test 2. The 401 error raised an exception instead of failing over to Groq."
  severity: major
  test: 3
  artifacts: []
  missing: []

- truth: "The application requires all 3 API keys to start, and hardcodes the provider list to always check Gemini, OpenRouter, and Groq."
  status: failed
  reason: "User requested enhancement: Make OpenRouter and Groq optional. Fallback logic should dynamically skip providers that do not have an API key configured, instead of crashing or wasting time retrying."
  severity: minor
  test: 4
  artifacts: []
  missing: []

- truth: "If a provider returns a 401 or 403 authorization error (e.g., due to an invalid key), the system immediately fails over to the next provider without attempting to retry."
  status: failed
  reason: "User reported: fail. The system crashes instead of failing over."
  severity: major
  test: 5
  artifacts: []
  missing: []
