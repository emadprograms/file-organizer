---
wave: 2
depends_on: ["01-PLAN.md"]
files_modified:
  - "src/llm_client.py"
  - "tests/test_llm_client.py"
autonomous: true
---

# Phase 01: Foundation & Infrastructure (Wave 2 - LLM Client)

## Goal
Build the centralized LLM client using the `google-genai` SDK with strict rate limiting and specific error handling backoff logic.

## Requirements Covered
- LLM-01: Centralized LLM client
- LLM-02: Model: Gemma 4 26B A4B IT for all calls
- LLM-03: Rate limiting: minimum 7 seconds between requests
- LLM-04: Error 400/404 → fail fast, abort program
- LLM-05: Error 500 → wait 15 seconds, retry
- LLM-06: Error 429 → wait 65 seconds, retry; fail entirely after 3 consecutive 429s
- LLM-07: Boundary detection 500s: shrink chunk size after 5 consecutive; fail at 10 consecutive
- LLM-08: Other LLM call 500s: skip item after 5 consecutive, log warning
- LLM-09: Error counters reset on ANY successful response

## Artifacts this phase produces
- `src/llm_client.py` (file)
- `src/llm_client.py:LLMClient` (class)
- `src/llm_client.py:LLMClient.__init__` (method)
- `src/llm_client.py:LLMClient.generate_content` (method)
- `src/llm_client.py:LLMRateLimitError` (exception)
- `src/llm_client.py:LLMServerError` (exception)
- `src/llm_client.py:LLMClientError` (exception)
- `tests/test_llm_client.py` (file)

<threat_model>
ASVS Level: 1
Block On: high
Threats:
- T-01: Resource exhaustion from uncontrolled API loops.
  Mitigation: Strict backoff parameters (15s for 500s, 65s for 429s) and max-retry abort constraints implemented in `llm_client.py`.
</threat_model>

## Tasks

<task id="02-01" read_first="src/llm_client.py">
  <action>Create `src/llm_client.py` and implement the `LLMClient` class using the `google-genai` SDK. Instantiate the Google GenAI client and enforce a synchronous 7-second rate limit between all `generate_content` calls using a token bucket or `time.sleep` mechanism. Default model must be `gemma-4-26b-a4b-it`.</action>
  <acceptance_criteria>
    - `pytest tests/test_llm_client.py` passes
    - Repeated calls to `generate_content` wait at least 7 seconds from the start of the previous call.
  </acceptance_criteria>
</task>

<task id="02-02" read_first="src/llm_client.py">
  <action>Implement error handling and retry logic in `LLMClient.generate_content` (using `tenacity` or custom logic). Specifically catch `google.genai.errors.APIError` to read the embedded HTTP status code. Map HTTP 400/404 to immediate fail (`LLMClientError`), HTTP 429 to 65s wait (max 3 retries, then fail), and HTTP 500 to 15s wait. The 7-second rate limiter must calculate wait duration based on the start time of the previous request to avoid drift. Error counters must reset on any successful response.</action>
  <acceptance_criteria>
    - `pytest tests/test_llm_client.py` passes
    - 400/404 errors raise an exception immediately (caught via `APIError`).
    - 429 errors wait 65s and fail after 3 consecutive attempts.
    - 500 errors wait 15s and retry.
  </acceptance_criteria>
</task>

<task id="02-03" read_first="src/llm_client.py">
  <action>Implement context-specific 500 handling via parameters in `LLMClient.generate_content` (e.g. `is_boundary_call=False`). If `is_boundary_call` is True, implement a callback or state flag to signal shrinking chunk size after 5 consecutive 500s, and hard fail after 10. If False, skip the item after 5 consecutive 500s by returning `None`, and ensure the caller is prepared to handle this empty return value gracefully without throwing exceptions.</action>
  <acceptance_criteria>
    - `pytest tests/test_llm_client.py` passes
    - Boundary calls fail after 10 consecutive 500s and signal shrink after 5.
    - Non-boundary calls skip after 5 consecutive 500s and return a safe `None` value instead of crashing.
  </acceptance_criteria>
</task>

## Verification
<verify>
  `pytest tests/test_llm_client.py` passes successfully with all error and rate-limiting paths tested.
</verify>

## Must Haves
must_haves:
  truths:
    - Centralized LLM client enforces 7s rate limit between calls (measurable via timestamps in logs).
    - LLM client handles 400→fail, 500→retry 15s, 429→retry 65s with correct consecutive error counting.
