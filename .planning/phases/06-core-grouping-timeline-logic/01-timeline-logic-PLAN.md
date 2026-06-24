---
wave: 1
depends_on: []
requirements: [LOGIC-01, LOGIC-02, LOGIC-03, LOGIC-04, LOGIC-05, LOGIC-06]
files_modified:
  - src/schemas.py
  - src/pipeline.py
  - tests/test_timeline_logic.py
autonomous: true
---

# Phase 06: Core Grouping & Timeline Logic

<threat_model>
ASVS_Level: 1
Block_On: High
Description: This phase introduces new file logic and data manipulation. Ensure no Path Traversal or memory overflow vulnerabilities are introduced through the prefix_buffer or verified_residents set.
</threat_model>

## Artifacts this phase produces
- Field `is_continuation` on `src/schemas.py::PageClassification`
- Method `_group_pages_into_documents` on `src/pipeline.py::Pipeline`
- Local variable `verified_residents` in `_group_pages_into_documents`
- Local variable `prefix_buffer` in `_group_pages_into_documents`
- File `tests/test_timeline_logic.py`
- Test functions `test_logic_01_large_family`, `test_logic_02_array_order`, `test_logic_03_single_word_names`, `test_logic_04_date_grouping`, `test_logic_05_prefix_rescue`, `test_logic_06_non_anchor_routing`

## must_haves

must_haves:
  truths:
    - D-01: Anchor documents with up to 10 names establish timelines.
    - Anchor documents preserve the timeline if any named person matches the current tenant.
    - Single-word Arabic names correctly overlap and match without failing the intersection threshold.
    - D-02: Documents only group if date matches exactly (with null-safety to prevent IndexError) OR `is_continuation` is True.
    - D-03: The LLM extraction and retry logic for is_continuation MUST respect rate limits, and fallback MUST log a warning.
    - D-04: Implement Verified Residents Pre-scan.
    - D-06: ID cards at the front of a file are buffered and retroactively assigned to the first anchor's tenant. If no anchor is found, they flush to the start of the final array to preserve chronology.
    - D-05: Non-anchor letters assigned to family members (via word intersection) collapse under the primary tenant's folder. Letters assigned to strangers (no word intersection) route to their own distinct folders.

## Tasks

```xml
<task>
  <read_first>
    <file>src/schemas.py</file>
    <file>src/pipeline.py</file>
  </read_first>
  <action>
    Add `is_continuation: bool = Field(default=False, description="True if this page is a continuation of the previous page, False otherwise")` to `PageClassification` in `src/schemas.py`.
    In `src/pipeline.py::process_single_page`, wrap `self.client.classify_page` in a `for attempt in range(3):` retry loop. If `InvalidResponseError` or `LLMFailureError` occurs, sleep using exponential backoff (e.g. `time.sleep(2 ** attempt)`) and retry. Only fallback to `Category.OTHER_LETTERS` and `UNKNOWN` resident if all 3 attempts fail. Also log a warning message indicating that the page parsing failed after 3 retries and is falling back to OTHER_LETTERS.
  </action>
  <acceptance_criteria>
    `PageClassification` schema accepts and defaults `is_continuation`.
    `process_single_page` successfully retries up to 3 times on `InvalidResponseError` and `LLMFailureError` before executing the fallback block.
    A logging warning is emitted when the fallback block executes.
  </acceptance_criteria>
</task>

<task>
  <read_first>
    <file>src/pipeline.py</file>
  </read_first>
  <action>
    Refactor Pass 2 of `process_pdf` into a standalone method `_group_pages_into_documents(self, raw_pages: list[tuple[int, PageClassification]], canonical_mapping_clean: dict[str, str]) -> list[DocumentGroup]`.
    Replace lines 164-225 in `process_pdf` with a call to `self._group_pages_into_documents(raw_pages, canonical_mapping_clean)`.
  </action>
  <acceptance_criteria>
    `_group_pages_into_documents` method exists on the `Pipeline` class and encapsulates the grouping loop.
    `process_pdf` correctly calls `_group_pages_into_documents` and returns its result without behavior change (yet).
  </acceptance_criteria>
</task>

<task>
  <read_first>
    <file>src/pipeline.py</file>
  </read_first>
  <action>
    Implement Verified Residents Pre-scan inside `_group_pages_into_documents`: iterate over `raw_pages` before the main loop, collect all canonical mapped names present on Anchor categories (`BASIC_DETAILS`, `KEY_HANDOVER`, `CONTRACT`), and save them to a `verified_residents` set.
    Implement Prefix Document Rescue: initialize `prefix_buffer: list[DocumentGroup] = []` for documents parsed while `current_primary_tenant == "UNKNOWN"`. When `current_primary_tenant` changes from "UNKNOWN" to a valid name, iterate over `prefix_buffer`, update their `primary_tenant`, and extend `documents`. If the loop finishes and timeline is still UNKNOWN, flush `prefix_buffer` to `documents` as UNKNOWN by prepending it (e.g., `documents = prefix_buffer + documents`) so early documents stay at the beginning.
  </action>
  <acceptance_criteria>
    `verified_residents` set correctly aggregates anchor names before Pass 2 loop.
    `prefix_buffer` safely holds early pages and retroactively applies the `primary_tenant` once an anchor establishes the timeline.
    `prefix_buffer` correctly flushes as UNKNOWN to the START of `documents` array if no anchor is ever found, maintaining chronological order.
  </acceptance_criteria>
</task>

<task>
  <read_first>
    <file>src/pipeline.py</file>
  </read_first>
  <action>
    Update `_group_pages_into_documents` matching logic (LOGIC-01, 02, 03, 04, 06):
    1. Change the limit `len(valid_mapped) <= 3` to `len(valid_mapped) <= 10`.
    2. Iterate `candidate in valid_mapped`. If `len(words_current.intersection(words_candidate)) >= min(2, len(words_current), len(words_candidate))` is True, retain `current_primary_tenant` and `break` to prevent hijacking. If no candidate matches, set `current_primary_tenant = valid_mapped[0]`.
    3. If document is NOT an anchor and has valid names, check if `valid_mapped[0]` is family (shares >= 2 words with `current_primary_tenant`). If family, `page_primary_tenant = current_primary_tenant` (collapse). If NOT family (stranger), `page_primary_tenant = valid_mapped[0]` (separate folder).
    4. Modify the group merge condition with null-safety: `(page.date and documents[-1].dates and documents[-1].dates[-1] == page.date) or page.is_continuation`.
  </action>
  <acceptance_criteria>
    Matching conditional successfully checks up to 10 names.
    Single-word names match correctly via `min(2, len(), len())` dynamic threshold.
    Array order does not hijack if a subsequent name matches the current tenant.
    Non-anchor pages correctly fallback to the current tenant if the candidate name is unverified.
    Consecutive pages merge safely (without IndexError on missing dates) if dates match exactly or `is_continuation` is True.
  </acceptance_criteria>
</task>

<task>
  <read_first>
    <file>src/pipeline.py</file>
    <file>.planning/phases/06-core-grouping-timeline-logic/06-RESEARCH.md</file>
  </read_first>
  <action>
    Create `tests/test_timeline_logic.py` using `pytest`.
    Implement unit tests that mock `raw_pages` (list of `(int, PageClassification)`) and call `Pipeline()._group_pages_into_documents(raw_pages, canonical_mapping_clean)`.
    Implement the 6 explicit test scenarios: `test_logic_01_large_family`, `test_logic_02_array_order`, `test_logic_03_single_word_names`, `test_logic_04_date_grouping`, `test_logic_05_prefix_rescue`, `test_logic_06_non_anchor_routing` (scenarios as detailed in 06-RESEARCH.md).
  </action>
  <acceptance_criteria>
    Command `pytest tests/test_timeline_logic.py` runs and passes.
    All 6 logic scenarios have dedicated assertions validating the new grouping behavior independent of the LLM pipeline.
  </acceptance_criteria>
</task>
```
