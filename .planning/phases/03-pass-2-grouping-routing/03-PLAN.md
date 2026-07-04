---
wave: 3
depends_on:
  - 02-PLAN.md
files_modified:
  - src/processing/grouping.py
autonomous: true
---

# Phase 3 - Plan 3: LLM Grouping Logic & Shrink Loop

## Requirements
- GRP-02: Boundary detection overlapping chunks
- GRP-03: LLM grouping rules (subject/topic shift only)

## Review Feedback Incorporation
- **process_with_shrink Iteration State (Antigravity - HIGH)**: Replaced static sliding window generator with a dynamic `while` loop tracking `current_page_index` to properly handle chunk shrinking mid-iteration without losing state.
- **LLM Boundary Prompt Risk (Gemini - MEDIUM)**: Added explicit few-shot examples to the prompt template demonstrating that a date change does NOT trigger a boundary, but a subject change DOES.

## Tasks

```xml
<task>
  <action>Define LLM Prompt Templates with Few-Shot Examples</action>
  <read_first>
    - src/processing/grouping.py
  </read_first>
  <acceptance_criteria>
    - Prompt string specifically instructs: "Boundaries ONLY on subject/content shift. DO NOT split on date changes or sender changes."
    - Prompt string includes at least one few-shot example showing a date change without a boundary.
    - Prompt string includes at least one few-shot example showing a clear subject shift resulting in a boundary.
  </acceptance_criteria>
</task>

<task>
  <action>Implement `process_with_shrink` using dynamic index tracking</action>
  <read_first>
    - src/processing/grouping.py
    - src/llm/llm.py
  </read_first>
  <acceptance_criteria>
    - `process_with_shrink(pages: list[PageData], llm_client)` processes all pages.
    - Uses a `while current_page_index < len(pages)` loop.
    - Shrinks chunk size (10 -> 5 -> 3) after 5 consecutive failures, ONLY triggering on `500 ServerError` or `ValidationError` (allowing 429 errors to be handled normally by the underlying LLM client) (satisfies D-03).
    - Hard fails (raises RuntimeError) after 10 total consecutive failures (satisfies D-03).
    - Calls `llm_client._route_llm_call(..., response_schema=GroupingResponse)`.
    - Calls `verify_groups` on the result. If validation fails, treats it as a failure for the shrink logic.
    - Merges chunks using `merge_chunks` when moving forward.
  </acceptance_criteria>
</task>
```

## Verification
- Code review confirms `process_with_shrink` handles iteration state explicitly via `current_page_index` incrementing by `chunk_size - overlap`.

## Must Haves
- The shrink loop must be stateful (dynamic index tracking) rather than a static generator.
- Prompt must explicitly demonstrate the negative constraint (no date boundaries).
- Must implement D-03 (Verification Failure Handling) with max 10 attempts and chunk shrinking.

## Artifacts this phase produces
- `process_with_shrink` (Function)
- `GROUPING_PROMPT` (Constant string)
