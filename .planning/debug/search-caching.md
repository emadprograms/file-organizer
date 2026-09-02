---
status: resolved
trigger: "the search mecahnism should have some kind of caching. it takes very long to load anything. the search should be fast."
updated: 2026-09-02
---

# Debug Session: search-caching

## Symptoms
- **Expected behavior**: Search should be fast and load instantly.
- **Actual behavior**: Search takes very long to load anything.
- **Error messages**: None.
- **Timeline**: Currently happening.
- **Reproduction**: Perform a search.

## Current Focus
- hypothesis: Search is slow because it reads from disk on every keystroke/request.
- test: Implemented an in-memory cache for search data to avoid disk I/O on every request.
- expecting: Faster search responses.
- next_action: "None"
- reasoning_checkpoint: Added an in-memory cache (`_SEARCH_CACHE`) in `src/api/routes.py` with a TTL of 300 seconds to build the searchable documents index just once per cache cycle. Tests confirm that the API endpoints and frontend UX tests pass without regressions.
- tdd_checkpoint: Tests in `tests/test_api.py` and `tests/frontend/test_search_ux.py` pass.

## Evidence
- timestamp: 2026-09-02T13:50:42+03:00
  - evidence: User reported search is slow and needs caching.
- timestamp: 2026-09-02T13:53:00+03:00
  - evidence: Replaced disk reading in `search()` with an in-memory cache function `get_search_index()`.

## Eliminated
- Disk IO bottleneck during search.
