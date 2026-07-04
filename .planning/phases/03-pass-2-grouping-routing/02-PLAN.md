---
wave: 2
depends_on:
  - 01-PLAN.md
files_modified:
  - src/processing/grouping.py
  - tests/test_grouping.py
autonomous: true
---

# Phase 3 - Plan 2: Grouping Engine & Verification

## Requirements
- GRP-01: Pre-split page sequence by category
- GRP-06: Programmatic verification (no gaps, overlaps, invented pages)
- GRP-07: Merge overlapping chunks

## Review Feedback Incorporation
- **Page Indexing Ambiguity (Gemini - LOW)**: Verification logic explicitly checks that bounds are 0-indexed and within the provided chunk slice.
- **Boundary Edge Case Test (Gemini - Suggestion)**: Added specific test for an exact boundary overlap to ensure `merge_chunks` behaves correctly.

## Tasks

```xml
<task>
  <action>Implement `category_presplit`</action>
  <read_first>
    - src/processing/grouping.py (create if needed)
  </read_first>
  <acceptance_criteria>
    - `category_presplit` takes a list of `PageData` and returns a `list[list[PageData]]`.
    - A new sublist is created every time `page.category` changes.
    - Test `test_category_presplit` verifies correct partitioning of pages.
  </acceptance_criteria>
</task>

<task>
  <action>Implement `verify_groups`</action>
  <read_first>
    - src/processing/grouping.py
  </read_first>
  <acceptance_criteria>
    - `verify_groups(groups: list[GroupEntry], chunk_start_idx: int, chunk_end_idx: int)` returns True if valid, raises ValueError if invalid.
    - Checks for gaps: `groups[0].start_page` == `chunk_start_idx` and `groups[i].end_page + 1` == `groups[i+1].start_page`.
    - Checks for overlaps: no overlapping ranges between consecutive groups.
    - Checks for invented pages: `groups[-1].end_page` == `chunk_end_idx - 1`.
    - Test `test_verification_logic` verifies it catches gaps, overlaps, and out-of-bounds indices.
  </acceptance_criteria>
</task>

<task>
  <action>Implement `merge_chunks`</action>
  <read_first>
    - src/processing/grouping.py
  </read_first>
  <acceptance_criteria>
    - `merge_chunks(chunk1_groups: list[DocumentGroup], chunk2_groups: list[DocumentGroup], overlap_page_idx: int)` returns merged list.
    - Merges groups if they both contain `overlap_page_idx`.
    - Trusts Chunk 1's metadata (`reason`, `brief_arabic_title`) for the merged group (satisfies D-01).
    - Test `test_overlap_merge` verifies boundary edge case where document spans exactly across chunk boundary.
  </acceptance_criteria>
</task>
```

## Verification
- `pytest tests/test_grouping.py` passes all unit tests for pure-Python functions.

## Must Haves
- Verification strictly enforces contiguous, non-overlapping coverage of the exact chunk page range.
- Must implement D-01 (Overlap Merge Resolution) by trusting the first chunk during merges.

## Artifacts this phase produces
- `category_presplit` (Function)
- `verify_groups` (Function)
- `merge_chunks` (Function)
- `tests/test_grouping.py` (New File)
