---
objective: "Implement LLM Grouping Call and Resilient Loop"
wave: 2
depends_on: [1]
files_modified:
  - src/llm/llm.py
  - src/processing/grouping.py
  - tests/test_llm_grouping.py
autonomous: true
requirements:
  - GRP-03
  - GRP-04
  - GRP-05
---

# Plan 2: LLM Grouping Call and Resilient Loop

## Objective
Implement the LLM call that asks the model to detect subject boundaries and generate Arabic titles for a chunk of pages. Build the `process_with_shrink` loop that orchestrates this call, retrying and shrinking the chunk size upon verification failures or 500 errors.

## Tasks

```xml
<task>
  <action>
    Add `group_chunk(self, pages: list, prompt_template: str = "") -> GroupingResponse` to `LLMClient` in `src/llm/llm.py`.
    Format the `pages` input into a text representation containing page index, date, tenant, category, and text content for the model to read.
    Use `_route_llm_call` specifying the `GroupingResponse` schema.
    Ensure the prompt strictly commands the LLM to group ONLY on subject/content shifts, ignoring date or sender changes.
  </action>
  <read_first>
    - src/llm/llm.py
    - src/core/schemas.py
  </read_first>
  <acceptance_criteria>
    - `group_chunk` is defined on `LLMClient`.
    - It returns a `GroupingResponse`.
    - It delegates to `_route_llm_call`.
  </acceptance_criteria>
</task>

<task>
  <action>
    Implement `process_with_shrink(pages: list, llm_client: LLMClient) -> list[GroupEntry]` in `src/processing/grouping.py`.
    It implements the 10->5->3 chunk shrinking logic:
    - Try to process `pages` using `generate_chunks` with `chunk_size`.
    - For each chunk, call `llm_client.group_chunk`.
    - Verify the response using `verify_groups`.
    - If `verify_groups` raises `InvalidResponseError` or the LLM call raises a `5xx` error, increment a consecutive failure counter.
    - If consecutive failures reach 5, shrink the `chunk_size` to the next level in `[10, 5, 3]`.
    - Hard fail (raise `RuntimeError`) if total consecutive failures hit 10.
    - On successful chunk processing, reset consecutive failures.
    - Returns the merged result using `merge_chunks` on all successful chunk results.
  </action>
  <read_first>
    - src/processing/grouping.py
    - src/llm/llm.py
  </read_first>
  <acceptance_criteria>
    - `process_with_shrink` correctly calls `group_chunk`, `verify_groups`, and `merge_chunks`.
    - Shrinks chunk sizes correctly after 5 consecutive failures.
    - Aborts with `RuntimeError` after 10 consecutive failures.
  </acceptance_criteria>
</task>

<task>
  <action>
    Write tests in `tests/test_llm_grouping.py` simulating the LLM client responses.
    Mock `LLMClient.group_chunk` to return valid responses, and test `process_with_shrink`'s success path.
    Mock `LLMClient.group_chunk` to raise exceptions, and test the shrink logic and the 10-failure hard fail limit.
  </action>
  <read_first>
    - tests/conftest.py
  </read_first>
  <acceptance_criteria>
    - `pytest tests/test_llm_grouping.py -x -q` exits 0.
  </acceptance_criteria>
</task>
```

## Verification
- Run `pytest tests/test_llm_grouping.py -x` and ensure all pass.

## Must Haves
- **Truths**:
  - `group_chunk` method added to `LLMClient` that yields `GroupingResponse`.
  - `process_with_shrink` implemented with 10->5->3 logic.
  - 10-consecutive-failures hard limit enforced.

## Artifacts this phase produces
- `src.llm.llm.LLMClient.group_chunk` (method)
- `src.processing.grouping.process_with_shrink` (function)
- `tests/test_llm_grouping.py` (test file)
