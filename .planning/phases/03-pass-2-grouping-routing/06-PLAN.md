---
objective: "Pipeline Integration for Pass 2"
wave: 6
depends_on: [5]
files_modified:
  - src/processing/pipeline.py
  - tests/test_pipeline_pass2.py
autonomous: true
requirements:
  - GRP-01
must_haves:
  truths:
    - Documents undergo end-to-end processing without unexpected crashes
    - The processing loop correctly pre-splits items to avoid cross-category overlaps
    - Generated documents match precisely with predefined routing mappings
  artifacts:
    - tests/test_pipeline_pass2.py
  key_links:
    - src/processing/pipeline.py relies on src/processing/grouping.py process_with_shrink
    - src/processing/pipeline.py relies on src/processing/routing.py determine_folder
---

# Plan 6: Pipeline Integration for Pass 2

## Objective
Wire the output of Pass 1.5 in `src/processing/pipeline.py` through the newly built Grouping and Routing modules, replacing the old declarative grouping logic, and hand off the result to `FileOrganizer`.

## Tasks

```xml
<task>
  <files>
    - tests/test_pipeline_pass2.py
  </files>
  <action>
    Create `tests/test_pipeline_pass2.py`.
    Write integration tests validating the end-to-end data flow of Pass 2, mocking `LLMClient` appropriately.
  </action>
  <verify>
    <automated>python -m pytest tests/test_pipeline_pass2.py -x</automated>
  </verify>
  <done>
    - Pipeline integration tests are defined and fail.
  </done>
</task>

<task>
  <files>
    - src/processing/pipeline.py
  </files>
  <action>
    Update `_group_pages_into_documents(self, raw_pages: list[tuple[int, PageData]], config: 'UserConfig') -> list[DocumentGroup]` in `src/processing/pipeline.py`.
    Remove the old declarative and script-based grouping logic entirely.
    Implement Step 1: Category Pre-Split (GRP-01). Iterate through `raw_pages` and split them into contiguous sub-sequences where both the `category` and the assigned `residents[0]` are identical. Any change is an automatic boundary.
  </action>
  <verify>
    <automated>python -m pytest tests/test_pipeline_pass2.py::test_category_presplit -x</automated>
  </verify>
  <done>
    - `_group_pages_into_documents` correctly segments `raw_pages` into contiguous runs of the same category and tenant.
  </done>
</task>

<task>
  <files>
    - src/processing/pipeline.py
  </files>
  <action>
    Implement Step 2 & 3 in `_group_pages_into_documents`: 
    For each sub-sequence from Step 1, call `process_with_shrink(sub_sequence, self.client)` from `src/processing/grouping.py`.
    Map each resulting `GroupEntry` into a `DocumentGroup` schema object.
    Set the `DocumentGroup`'s `start_page`, `end_page`, `reason`, `brief_arabic_title`.
    The `primary_tenant`, `category`, and `dates` should be extracted from the source `PageData` elements covered by the group's page range.
    For each final `DocumentGroup`, call `route_document(doc, self.client)` from `src/processing/routing.py` to get the target folder and whether it was direct-routed.
    Set `doc.folder_path` and `doc.is_direct_routed` accordingly.
  </action>
  <verify>
    <automated>python -m pytest tests/test_pipeline_pass2.py::test_routing_integration -x</automated>
  </verify>
  <done>
    - `process_with_shrink` is successfully called for each category run.
    - Every returned `DocumentGroup` has `folder_path` populated with a valid folder name from the 13 hardcoded folders.
    - Final result is a flat `list[DocumentGroup]` accurately reflecting the LLM's grouping decisions.
  </done>
</task>
```
