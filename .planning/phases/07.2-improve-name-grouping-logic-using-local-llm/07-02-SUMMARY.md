# Phase 07.2: Improve name grouping logic using local LLM
**Plan:** 07-02-PLAN.md
**Status:** COMPLETE

## What was built
We successfully refactored the name grouping logic in the Arabic Document Categorizer to leverage a dual-check approach for entity resolution:
1. **Schema Update:** Added `NameMatchResult` to `src/schemas.py` to enforce structured JSON output for the LLM matcher, ensuring it returns `is_match` and `reason`.
2. **LLM Method:** Implemented `check_name_match` inside `src/llm.py`'s `GemmaClient`.
   - Annotated with `@functools.lru_cache(maxsize=1024)` to eliminate redundant API calls for duplicate name pairs across pages.
   - Instructs the local `Qwen2-VL` model to disregard Arabic prefixes (like "ال") and titles (like "السيد").
   - Added robust error handling explicitly catching `ConnectionError` and `TimeoutError` in addition to validation failures.
   - Triggers the `gemini-4-26b` cloud fallback seamlessly if the local server fails.
3. **Pipeline Refactor:** Updated the entity grouping loops in `src/pipeline.py` (Pass 2 - Tenant Grouping) to preserve the exact set-intersection match as a "Fast Path". When this strict match fails, the pipeline now consults `self.client.check_name_match` to make the final semantic decision.

## Deviations
- None. The implementation closely followed the reviewed plan.

## Outstanding issues
- None. Syntax validation passed, and the dual-layer LLM matching strategy provides high resilience.
