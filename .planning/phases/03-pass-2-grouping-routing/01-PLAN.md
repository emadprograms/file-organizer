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
must_haves:
  truths:
    - GroupEntry and GroupingResponse schemas exist
    - generate_chunks yields overlapping segments
    - verify_groups strictly catches non-contiguous coverage
    - merge_chunks joins chunks cleanly without duplicating pages
  artifacts:
    - src.core.schemas.GroupEntry
    - src.core.schemas.GroupingResponse
    - src.processing.grouping.generate_chunks
    - src.processing.grouping.verify_groups
    - src.processing.grouping.merge_chunks
    - tests/test_grouping.py
  key_links: []
---

# Plan 1: Grouping Utilities and Schemas

## Objective
Establish the foundational data structures and pure-Python grouping algorithms for Pass 2, including the overlapping chunk generator, verification logic, and chunk merging.

## Tasks

```xml
<task>
  <files>
    - tests/test_grouping.py
  </files>
  <action>
    Create `tests/test_grouping.py`.
    Write tests for `generate_chunks` (testing sliding window with overlaps), `verify_groups` (testing gaps, overlaps, and invented pages), and `merge_chunks` (testing that overlap pages are resolved by trusting Chunk 1).
  </action>
  <verify>
    <automated>python -m pytest tests/test_grouping.py -x</automated>
  </verify>
  <done>
    - Tests for grouping utilities are fully defined and fail (since implementation is not written yet).
  </done>
</task>

<task>
  <files>
    - src/core/schemas.py
  </files>
  <action>
    Add `GroupEntry` and `GroupingResponse` models to `src/core/schemas.py`.
    `GroupEntry` needs fields: `start_page: int`, `end_page: int`, `reason: str`, `brief_arabic_title: str`.
    `GroupingResponse` needs field: `groups: list[GroupEntry]`.
    Extend existing `DocumentGroup` in `src/core/schemas.py` to include `reason: str | None = None`, `brief_arabic_title: str | None = None`, and `folder_path: str | None = None`.
  </action>
  <verify>
    <automated>python -c "from src.core.schemas import GroupEntry, GroupingResponse, DocumentGroup"</automated>
  </verify>
  <done>
    - `src/core/schemas.py` contains `GroupEntry` with specified fields.
    - `src/core/schemas.py` contains `GroupingResponse` with specified fields.
    - `DocumentGroup` includes `reason`, `brief_arabic_title`, and `folder_path` as optional fields.
  </done>
</task>

<task>
  <files>
    - src/processing/grouping.py
  </files>
  <action>
    Create `src/processing/grouping.py`.
    Implement `generate_chunks(pages: list, chunk_size: int = 10, overlap: int = 1)`.
    It should yield tuples of `(chunk_pages, is_overlap_with_prev)`. A sliding window that yields a subsequence of pages with a 1-page overlap with the preceding chunk.
  </action>
  <verify>
    <automated>python -m pytest tests/test_grouping.py::test_chunk_generator_overlap -x</automated>
  </verify>
  <done>
    - `src/processing/grouping.py` has a `generate_chunks` generator function.
    - For `pages=[0,1,2,3,4]`, `chunk_size=3`, `overlap=1`, it yields `([0,1,2], False)` then `([2,3,4], True)`.
  </done>
</task>

<task>
  <files>
    - src/processing/grouping.py
    - src/llm/llm.py
  </files>
  <action>
    Implement `verify_groups(groups: list[GroupEntry], chunk_start_page: int, chunk_end_page: int) -> bool` in `src/processing/grouping.py`.
    It must check for contiguous coverage of the chunk's range (no gaps, no overlaps between groups, and no invented pages outside the chunk).
    Return `True` if valid, raise `InvalidResponseError` (from `src.llm.llm`) with a descriptive message if invalid.
  </action>
  <verify>
    <automated>python -m pytest tests/test_grouping.py::test_verification_logic -x</automated>
  </verify>
  <done>
    - `verify_groups` raises error if a gap exists between groups.
    - `verify_groups` raises error if groups overlap.
    - `verify_groups` raises error if group indices fall outside `[chunk_start_page, chunk_end_page]`.
    - Returns `True` for perfect contiguity.
  </done>
</task>

<task>
  <files>
    - src/processing/grouping.py
  </files>
  <action>
    Implement `merge_chunks(chunk_results: list[list[GroupEntry]]) -> list[GroupEntry]` in `src/processing/grouping.py`.
    Given a list of verified group arrays (one array per chunk), merge them into a single list.
    When the overlap page (e.g., page 10) appears at the end of Chunk N and the start of Chunk N+1, trust Chunk N's grouping metadata. If the overlap page belongs to a multi-page group in Chunk N, and is the start of a group in Chunk N+1, extend Chunk N's group to cover Chunk N+1's group and discard Chunk N+1's metadata for that segment.
  </action>
  <verify>
    <automated>python -m pytest tests/test_grouping.py::test_overlap_merge -x</automated>
  </verify>
  <done>
    - `merge_chunks` correctly joins groups across chunk boundaries without duplicating the overlap page.
    - Metadata (`reason`, `brief_arabic_title`) from the earlier chunk takes precedence on the overlap page.
  </done>
</task>
```

## Artifacts this phase produces
- `src.core.schemas.GroupEntry` (dataclass/model)
- `src.core.schemas.GroupingResponse` (dataclass/model)
- `src.processing.grouping.generate_chunks` (function)
- `src.processing.grouping.verify_groups` (function)
- `src.processing.grouping.merge_chunks` (function)
- `tests/test_grouping.py` (test file)
