# Phase 3 Plan 3 - LLM Grouping Logic & Shrink Loop

## Completed Tasks
1. **Define LLM Prompt Templates with Few-Shot Examples**: Added `GROUPING_PROMPT` in `src/processing/grouping.py` with explicit rules ("ONLY on subject/content shift. DO NOT split on date changes or sender changes") and few-shot examples illustrating correct handling of date vs. subject shifts.
2. **Implement `process_with_shrink` using dynamic index tracking**: Implemented the boundary detection loop tracking `current_page_index` and chunk boundaries. The logic correctly handles calling `llm_client._route_llm_call`, verifies the response with `verify_groups`, merges overlapping chunks, and implements the required chunk-shrinking logic (10 -> 5 -> 3) on validation/server errors up to a maximum of 10 total failures.

## Next Steps
- Implement folder routing logic (Phase 3 Plan 4) or proceed with integration testing.
