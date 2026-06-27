---
status: testing
phase: 03-cloud-fallback
source: 03-SUMMARY.md
started: 2026-06-27T19:23:05+03:00
updated: 2026-06-27T19:23:05+03:00
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 1
name: Normal Gemini Request
expected: |
  The application categorizes a file correctly using the primary Gemini provider when API keys are valid, returning valid JSON without invoking fallbacks.
awaiting: user response

## Tests

### 1. Normal Gemini Request
expected: The application categorizes a file correctly using the primary Gemini provider when API keys are valid, returning valid JSON without invoking fallbacks.
result: [pending]

### 2. Fallback to OpenRouter
expected: When the Gemini API fails (e.g. due to simulated 5xx or invalid Gemini key but valid OpenRouter key), the system automatically falls back to OpenRouter. The request succeeds and returns valid JSON.
result: [pending]

### 3. Fallback to Groq
expected: When both Gemini and OpenRouter fail (e.g. due to invalid keys), the system automatically falls back to Groq. The request succeeds and returns valid JSON.
result: [pending]

### 4. 429 Rate Limit Retry
expected: When the active provider returns a 429 Rate Limit error, the system pauses for approximately 65 seconds and retries the request with the same provider before failing over.
result: [pending]

### 5. Fail Fast on Auth Errors
expected: If a provider returns a 401 or 403 authorization error (e.g., due to an invalid key), the system immediately fails over to the next provider without attempting to retry.
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0

## Gaps
