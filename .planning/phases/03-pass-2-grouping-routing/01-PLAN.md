---
objective: "Implement Grouping Utilities and Schemas"
wave: 1
depends_on: []
files_modified:
  - src/core/schemas.py
  - src/processing/grouping.py
  - tests/test_grouping.py
autonomous: true
requirements:
  - GRP-01
  - GRP-02
  - GRP-06
  - GRP-07
---

# Plan 1: Grouping Utilities and Schemas

## Objective
Establish the foundational data structures and pure-Python grouping algorithms for Pass 2, including the overlapping chunk generator, verification logic, and chunk merging.

## Tasks

```xml
<task>
  <action>
    Add `GroupEntry` and `GroupingResponse` models to `src/core/schemas.py`.
    `GroupEntry` needs fields: `start_page: int`, `end_page: int`, `reason: str`, `brief_arabic_title: str`.
    `GroupingResponse` needs field: `groups: list[GroupEntry]`.
    Extend existing `DocumentGroup` in `src/core/schemas.py` to include `reason: str | None = None`, `brief_arabic_title: str | None = None`, and `folder_path: str | None = None`.
  </action>
  <read_first>
    - src/core/schemas.py
  </read_first>
  <acceptance_criteria>
    - `src/core/schemas.py` contains `GroupEntry` with specified fields.
    - `src/core/schemas.py` contains `GroupingResponse` with specified fields.
    - `DocumentGroup` includes `reason`, `brief_arabic_title`, and `folder_path` as optional fields.
  </acceptance_criteria>
</task>

<task>
  <action>
    Create `src/processing/grouping.py`.
    Implement `generate_chunks(pages: list, chunk_size: int = 10, overlap: int = 1)`.
    It should yield tuples of `(chunk_pages, is_overlap_with_prev)`. A sliding window that yields a subsequence of pages with a 1-page overlap with the preceding chunk.
  </action>
  <read_first>
    - .planning/phases/03-pass-2-grouping-routing/03-RESEARCH.md
  </read_first>
  <acceptance_criteria>
    - `src/processing/grouping.py` has a `generate_chunks` generator function.
    - For `pages=[0,1,2,3,4]`, `chunk_size=3`, `overlap=1`, it yields `([0,1,2], False)` then `([2,3,4], True)`.
  </acceptance_criteria>
</task>

<task>
  <action>
    Implement `verify_groups(groups: list[GroupEntry], chunk_start_page: int, chunk_end_page: int) -> bool` in `src/processing/grouping.py`.
    It must check for contiguous coverage of the chunk's range (no gaps, no overlaps between groups, and no invented pages outside the chunk).
    Return `True` if valid, raise `InvalidResponseError` with a descriptive message if invalid.
  </action>
  <read_first>
    - src/processing/grouping.py
    - src/llm/llm.py (for InvalidResponseError)
  </read_first>
  <acceptance_criteria>
    - `verify_groups` raises error if a gap exists between groups.
    - `verify_groups` raises error if groups overlap.
    - `verify_groups` raises error if group indices fall outside `[chunk_start_page, chunk_end_page]`.
    - Returns `True` for perfect contiguity.
  </acceptance_criteria>
</task>

<task>
  <action>
    Implement `merge_chunks(chunk_results: list[list[GroupEntry]]) -> list[GroupEntry]` in `src/processing/grouping.py`.
    Given a list of verified group arrays (one array per chunk), merge them into a single list.
    When the overlap page (e.g., page 10) appears at the end of Chunk N and the start of Chunk N+1, trust Chunk N's grouping metadata. If the overlap page belongs to a multi-page group in Chunk N, and is the start of a group in Chunk N+1, extend Chunk N's group to cover Chunk N+1's group and discard Chunk N+1's metadata for that segment.
  </action>
  <read_first>
    - src/processing/grouping.py
  </read_first>
  <acceptance_criteria>
    - `merge_chunks` correctly joins groups across chunk boundaries without duplicating the overlap page.
    - Metadata (`reason`, `brief_arabic_title`) from the earlier chunk takes precedence on the overlap page.
  </acceptance_criteria>
</task>

<task>
  <action>
    Write tests in `tests/test_grouping.py` for `generate_chunks`, `verify_groups`, and `merge_chunks`.
  </action>
  <read_first>
    - src/processing/grouping.py
    - tests/conftest.py
  </read_first>
  <acceptance_criteria>
    - `pytest tests/test_grouping.py -x -q` exits 0.
    - Tests cover gaps, overlaps, and invented pages in `verify_groups`.
    - Tests cover the overlap page resolution in `merge_chunks`.
  </acceptance_criteria>
</task>
```

## Verification
- Run `pytest tests/test_grouping.py -x` and ensure all pass.

## Must Haves
- **Truths**:
  - `GroupEntry` and `GroupingResponse` schemas exist.
  - `generate_chunks` yields overlapping segments.
  - `verify_groups` strictly catches non-contiguous coverage.
  - `merge_chunks` joins chunks cleanly without duplicating pages.

## Artifacts this phase produces
- `src.core.schemas.GroupEntry` (dataclass/model)
- `src.core.schemas.GroupingResponse` (dataclass/model)
- `src.processing.grouping.generate_chunks` (function)
- `src.processing.grouping.verify_groups` (function)
- `src.processing.grouping.merge_chunks` (function)
- `tests/test_grouping.py` (test file)
