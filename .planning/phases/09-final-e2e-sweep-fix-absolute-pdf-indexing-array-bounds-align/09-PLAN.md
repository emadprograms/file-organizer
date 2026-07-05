---
wave: 1
depends_on: []
requirements:
  - CLN-08
  - GRP-06
  - LOG-02
  - OUT-06
files_modified:
  - "src/core/indexing.py"
  - "src/logger.py"
  - "src/llm/llm.py"
  - "src/processing/pipeline.py"
  - "src/processing/split.py"
  - "src/processing/routing.py"
  - "tests/test_indexing.py"
  - "tests/test_llm.py"
  - "tests/test_pipeline.py"
  - "tests/test_routing.py"
autonomous: true
---

# Phase 09 Plan

## Tasks

<task>
<action>
Create `src/core/indexing.py` containing `to_0_based(index: int) -> int`, `to_1_based(index: int) -> int`, and `validate_bounds(index: int, max_len: int) -> int`. Update `src/processing/split.py`'s `extract_pdf_segment` and `src/processing/pipeline.py` to use these validation functions before executing `fitz.insert_pdf` slicing. Create unit tests in `tests/test_indexing.py`.
</action>
<read_first>
- `src/processing/split.py`
- `src/processing/pipeline.py`
</read_first>
<acceptance_criteria>
- `tests/test_indexing.py` contains tests for normal, out-of-bounds, and edge indices that pass via `pytest`.
- `extract_pdf_segment` in `src/processing/split.py` contains calls to `validate_bounds` and `to_0_based`.
</acceptance_criteria>
</task>

<task>
<action>
Update `src/logger.py` to initialize a `logs/traces/` subdirectory. Update `src/llm/llm.py`'s `_route_llm_call` (or equivalent method) to write the JSON payload to `logs/traces/{run_id}_{timestamp}.json` for successful calls, and `logs/traces/{run_id}_{timestamp}.error.json` for exceptions/schema errors. Extract `response.usage_metadata.total_token_count` from the Google GenAI response and log it at INFO level.
</action>
<read_first>
- `src/logger.py`
- `src/llm/llm.py`
</read_first>
<acceptance_criteria>
- `src/logger.py` contains `os.makedirs(os.path.join(log_dir, "traces"), exist_ok=True)` or equivalent path creation.
- `src/llm/llm.py` contains `logger.info` or similar logging call outputting the token usage metadata.
- `tests/test_llm.py` (or equivalent test file) asserts that `.json` and `.error.json` trace files are successfully created.
</acceptance_criteria>
</task>

<task>
<action>
Update `src/processing/pipeline.py` date inference logic (`_interpolate_dates` or equivalent) to ensure all dates are fully resolved to absolute values. Add an explicit check at the end of Pass 1 ensuring no page has a `None` date before passing into Pass 2. If any page remains `None` after nearest-neighbor inference, assign a fallback or route it to "Unassigned".
</action>
<read_first>
- `src/processing/pipeline.py`
</read_first>
<acceptance_criteria>
- `src/processing/pipeline.py` contains an explicit loop/check for `None` dates at the end of Pass 1.
- Tests in `tests/test_pipeline.py` assert Pass 2 input data has zero `None` dates.
</acceptance_criteria>
</task>

<task>
<action>
Update `src/processing/routing.py`'s `route_document` to catch index/bounds exceptions and return `"Unassigned", False` as a safe fallback instead of crashing. Update the final reconciliation check in `src/processing/pipeline.py` (`process_pdf`) to throw a fatal `RuntimeError` if the sum of output pages does not exactly match the input pages.
</action>
<read_first>
- `src/processing/pipeline.py`
- `src/processing/routing.py`
</read_first>
<acceptance_criteria>
- `route_document` contains a `try...except IndexError` (or similar bounds exception) block returning `"Unassigned"`.
- `process_pdf` contains `raise RuntimeError` or similar fatal exception if total output pages mismatch total input pages.
- Deliberately dropping a page in `tests/test_pipeline.py` triggers the fatal reconciliation failure exception.
- `tests/test_pipeline.py` contains an E2E test using a fixture with out-of-bounds indexing in the JSON payload, verifying that the pipeline gracefully routes the edge case to the "Unassigned" folder without crashing.
</acceptance_criteria>
</task>

<task>
<action>
Fix verification gaps:
1. In `src/processing/routing.py`, change the fallback return value in the `IndexError` exception handler within `route_document` from `"13_others", False` to `"Unassigned", False`.
2. In `tests/test_pipeline.py`, add the missing E2E test that uses a fixture with out-of-bounds indexing in the JSON payload and asserts that the pipeline gracefully routes the document to the "Unassigned" folder.
3. In `tests/test_routing.py`, add a unit test for `route_document` that triggers an `IndexError` and asserts the return value is `"Unassigned", False`.
</action>
<read_first>
- `src/processing/routing.py`
- `tests/test_routing.py`
- `tests/test_pipeline.py`
</read_first>
<acceptance_criteria>
- `src/processing/routing.py` contains `"Unassigned", False` in the `IndexError` except block.
- `pytest tests/test_routing.py` passes and tests the index error fallback.
- `pytest tests/test_pipeline.py` passes and contains an out-of-bounds indexing E2E test.
</acceptance_criteria>
</task>

## must_haves

```yaml
must_haves:
  truths:
    - "D-01: D-04: Pipeline standardizes on 0-based indexing internally and 1-based externally."
    - "D-05: D-06: D-07: LLMClient writes trace files to logs/traces/ and logs token usage."
    - "Pass 1 resolves all dates absolutely."
    - "D-03: Reconciliation fails completely if pages are dropped."
    - "D-02: D-08: D-10: Runtime safe defaults route out-of-bounds index failures to Unassigned."
```

## Artifacts this phase produces

- `src/core/indexing.py`
- `tests/test_indexing.py`
- `to_0_based`
- `to_1_based`
- `validate_bounds`
- `tests/test_routing.py`
- `test_route_document_index_error`
- `test_pipeline_out_of_bounds_routing`
