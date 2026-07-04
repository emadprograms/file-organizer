---
objective: "Implement Grouping Algorithms"
wave: 1
depends_on: [1]
files_modified:
  - src/processing/grouping.py
autonomous: true
requirements:
  - GRP-02
  - GRP-06
  - GRP-07
must_haves:
  truths:
    - generate_chunks yields overlapping segments
    - verify_groups strictly catches non-contiguous coverage
    - merge_chunks joins chunks cleanly without duplicating pages
  artifacts:
    - src.processing.grouping.generate_chunks
    - src.processing.grouping.verify_groups
    - src.processing.grouping.merge_chunks
  key_links: []
---

# Plan 2: Grouping Algorithms

## Objective
Implement the pure-Python grouping algorithms for Pass 2: overlapping chunk generation, verification logic, and chunk merging.

## Tasks

```xml
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
