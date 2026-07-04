---
objective: "Implement Grouping Schemas and Tests"
wave: 1
depends_on: []
files_modified:
  - tests/test_grouping.py
  - src/core/schemas.py
autonomous: true
requirements:
  - GRP-04
  - GRP-05
must_haves:
  truths:
    - GroupEntry and GroupingResponse schemas exist
    - tests for grouping logic are defined
  artifacts:
    - src.core.schemas.GroupEntry
    - src.core.schemas.GroupingResponse
    - tests/test_grouping.py
  key_links: []
---

# Plan 1: Grouping Schemas and Tests

## Objective
Establish the foundational data structures for Pass 2 and define the unit tests for the pure-Python grouping algorithms.

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
```
