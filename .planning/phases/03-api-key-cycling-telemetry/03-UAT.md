---
status: partial
phase: 03-api-key-cycling-telemetry
source: [03-SUMMARY.md]
started: 2026-06-23T19:15:00Z
updated: 2026-06-23T19:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Global IP RPM Limit Enforced
expected: When processing a large PDF (>15 pages), the system should pause (stagger) exactly when 15 requests have been made within 60 seconds, preventing 429 API errors.
result: pass

### 2. Invalid LLM Response Handling
expected: If the LLM returns unparseable JSON or an invalid response twice for a page, the pipeline should gracefully log it and fall back to the `other_letters` category without crashing.
result: issue
reported: "The code tracks invalid_retries += 1 but never checks if it's >= 2. It retries 7 times and crashes with Max retries reached."
severity: major

### 3. Exponential Backoff on 429
expected: If an API key hits a 429 quota error, the system applies an exponential sleep penalty (with random jitter) and prints "Staggering... Thread sleeping for Xs".
result: pass

### 4. Rate Limiter Amnesia Fix (Global IP Freeze)
expected: If the user stops the GUI run and starts it again, or if a global 429 IP ban is detected, the system globally freezes for 65 seconds across all 44 keys rather than entering a rapid retry death spiral.
result: issue
reported: "not sure abut this. you'll have to build a test file for this and put all the test files in the tests folder so that in the future these features don't break. don't make scratch files."
severity: major

## Summary

total: 4
passed: 2
issues: 2
pending: 0
skipped: 0

## Gaps

- truth: "If the LLM returns unparseable JSON or an invalid response twice for a page, the pipeline should gracefully log it and fall back to the `other_letters` category without crashing."
  status: failed
  reason: "User reported: The code tracks invalid_retries += 1 but never checks if it's >= 2. It retries 7 times and crashes with Max retries reached."
  severity: major
  test: 2
  artifacts: []
  missing: []
- truth: "If the user stops the GUI run and starts it again, or if a global 429 IP ban is detected, the system globally freezes for 65 seconds across all 44 keys rather than entering a rapid retry death spiral."
  status: failed
  reason: "User reported: not sure abut this. you'll have to build a test file for this and put all the test files in the tests folder so that in the future these features don't break. don't make scratch files."
  severity: major
  test: 4
  artifacts: []
  missing: []

