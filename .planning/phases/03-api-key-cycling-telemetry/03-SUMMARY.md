---
phase: 03-api-key-cycling-telemetry
plan: 03
subsystem: api
tags: [gemma, rate-limit, backoff, concurrency]

# Dependency graph
requires:
  - phase: 02
    provides: [basic pipeline logic]
provides:
  - Enforced global 15 RPM IP-level cap
  - Sequential pipeline with key rotation
  - Exponential backoff with jitter on API limits
  - Graceful handling of invalid LLM responses
  - Routing of NONE-resident retry through the rate limiter
affects: [execution, reliability]

# Tech tracking
tech-stack:
  added: []
  patterns: [rate limiting, exponential backoff, jitter, telemetry]

key-files:
  created: []
  modified: [src/llm.py, src/pipeline.py]

key-decisions:
  - "Changed pipeline concurrency to sequential (1 worker) due to strict 15 RPM IP limit, while retaining multi-key daily quota rotation."
  - "Implemented exponential backoff with jitter to prevent cascading 429 errors into 500 server errors."
  - "Added logic to abort page retries after 2 invalid LLM responses to avoid wasting rate-limit slots."
  - "Enforced global 15 RPM cap across all keys combined."

patterns-established:
  - "Rate Limit Guard: Centralized control in _get_client_and_key via global_rpm_tracker and lock-free sleeps."
  - "Telemetry Reporting: Exact token counts for both successful and invalid responses."

requirements-completed: [REQ-HARD-01, REQ-HARD-03]

# Metrics
duration: 12 min
completed: 2026-06-23T17:15:00Z
status: complete
---

# Phase 03 Plan 03: Gap Closure Summary

**Hardened API rate limits and telemetry with global IP RPM cap, sequential pipeline processing, and exponential backoff**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-23T17:08:25Z
- **Completed:** 2026-06-23T17:15:00Z
- **Tasks:** 5
- **Files modified:** 2

## Accomplishments
- Enforced a strict global 15 requests/minute IP-level cap across all keys.
- Handled invalid 245-token LLM responses gracefully by falling back to OTHER_LETTERS after 2 failures.
- Routed all API retries (including the NONE-resident retry) through the rate limiter.
- Switched the multiprocessing pipeline to a sequential process to eliminate lock contention, since throughput is capped by the 15 RPM limit anyway.
- Implemented exponential backoff with jitter up to 300 seconds and permanently retired keys that reach 10 strikes.

## Task Commits

Each task was committed atomically:

1. **Task 03-04-01: Enforce Global 15 RPM IP-Level Cap** - `ec531e3` (feat)
2. **Task 03-04-02: Route NONE-Resident Retry Through Rate Limiter** - `4fb982d` (feat)
3. **Task 03-04-03: Fix Concurrency — Sequential Pipeline With Key Rotation** - `897fd95` (feat)
4. **Task 03-04-04: Handle Invalid Responses Gracefully** - `5a13a86` (feat)
5. **Task 03-04-05: Add Exponential Backoff With Jitter on 429s** - `53ca0c4` (feat)

**Plan metadata:** `pending` (docs: complete plan)

## Files Created/Modified
- `src/llm.py` - Added global RPM tracker, exponential backoff, invalid response handling.
- `src/pipeline.py` - Switched to sequential processing.

## Decisions Made
- Concurrency removed in favor of sequential processing since global RPM cap is 15.
- Exponential backoff uses 15s * 2^(strikes-1) capped at 300s, with +/- 50% jitter.
- Max invalid retries is set to 2 to prevent wasting rate limits on unparseable pages.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Gap closure complete. The application is now ready to reliably process documents at the 15 RPM limit without triggering 429/500 storms.

---
*Phase: 03-api-key-cycling-telemetry*
*Completed: 2026-06-23*
