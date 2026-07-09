# Summary: Refactor chunk merging to Anchor Page strategy (Plan 03)

## Objective
Refactored the chunk merging logic to use an "Anchor Page" strategy, ensuring that merged documents respect LLM-validated boundaries rather than simple mathematical overlap.

## Changes
- **src/processing/grouping/utils.py**:
    - Updated `merge_chunks` to identify the `DocumentGroup` containing the `overlap_page_idx` (anchor page) in both chunks.
    - Implemented boundary validation: merging only occurs if both chunks agree on whether the anchor page is a continuation or a boundary.
    - Implemented conflict resolution: if decisions conflict, the logic defaults to splitting the document at the chunk boundary, trusting Chunk 2 for the start of the new segment and truncating Chunk 1's group to prevent overlaps.
- **tests/test_grouping.py**:
    - Added `test_anchor_page_merging` covering:
        - Scenario A: Continuation -> Successful merge.
        - Scenario B: Agreed boundary -> Successful split.
        - Scenario C: Conflict (Continuing vs Boundary) -> Split at boundary.
        - Scenario D: Conflict (Boundary vs Continuing) -> Split at boundary.

## Verification Results
- `pytest tests/test_grouping.py::test_anchor_page_merging` passed.
- Confirmed that no overlaps are introduced in the resulting group list during conflict resolution.

## Outcome
Merging logic is now LLM-boundary driven, preventing blind merging of unrelated documents that happen to overlap.
