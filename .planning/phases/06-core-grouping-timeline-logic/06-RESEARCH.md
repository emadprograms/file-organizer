# Phase 6: Core Grouping & Timeline Logic - Research

## What do I need to know to PLAN this phase well?

1. **Refactoring Pass 2 is Highly Recommended:** Currently, `src/pipeline.py`'s `process_pdf` contains both Pass 1 (LLM extraction) and Pass 2 (Grouping logic) tightly coupled. To effectively test Phase 6 logic without invoking the LLM, you must extract the Pass 2 logic (from line 164 onwards) into a separate, unit-testable method like `_group_pages_into_documents(raw_pages, canonical_mapping)`.
2. **Schema Update Required:** You need to add an `is_continuation: bool` field to `PageClassification` in `src/schemas.py`. Because this modifies Pass 1, existing `.cache.json` files may throw validation errors if they lack this field, unless handled gracefully.
3. **Retries & Rate Limits (D-03):** Currently, `process_pdf` silently swallows `InvalidResponseError` (e.g., if `is_continuation` is missing) and uses a fallback (around Line 105). You will need to introduce a retry loop for Pass 1 that respects the existing 15 RPM global cap.
4. **Verified Residents Pre-Scan (LOGIC-06):** You must add an intermediate loop before Pass 2 begins to scan all `raw_pages`, aggregate names from Anchor documents, and populate a `verified_residents` set.
5. **Buffer Implementation (LOGIC-05):** Introduce a queue/buffer for documents processed while `current_primary_tenant == "UNKNOWN"`. If an anchor sets the timeline, flush the buffer by updating their `primary_tenant` and moving them to the main `documents` list. If the loop finishes and it's still unknown, flush them to "UNKNOWN".
6. **Adjusting Match Thresholds:** 
   - Changing the family size limit from 3 to 10 (LOGIC-01) is a simple integer swap on line 190.
   - Fixing single-word matching (LOGIC-03) requires replacing the static `< 2` word intersection threshold with a dynamic check (e.g., `< min(2, len(words_current), len(words_candidate))`).
7. **Array Order Independence (LOGIC-02):** The logic currently only compares against `valid_mapped[0]`. You must iterate through all names in `valid_mapped` to see if *any* name has sufficient word overlap with the `current_primary_tenant`.
8. **Date Grouping Override (LOGIC-04):** The `if` condition to merge consecutive pages into a document group (Line 206) must be updated to mandate exact date matching UNLESS `page.is_continuation` is True.

---

## Codebase Analysis & Integration Points

### 1. `src/schemas.py` Modifications
- **`PageClassification` schema:** Add a new boolean field `is_continuation` with a descriptive Pydantic prompt so the model accurately detects multi-page flows.

### 2. `src/pipeline.py` Modifications
- **LOGIC-01 (Family Size Resilience):** Change `len(valid_mapped) <= 3` to `10` on Line 190.
- **LOGIC-02 (Array Order Independence):** Lines 191-197. Stop testing just `candidate = valid_mapped[0]`. Iterate over `candidate in valid_mapped` and if an overlap is found, preserve the timeline and break.
- **LOGIC-03 (Accurate Name Matching):** Update Line 196 threshold to handle length-1 word lists.
- **LOGIC-04 (Precise Date Grouping):** Modify lines 206-208 to include `and (page.is_continuation or documents[-1].dates[-1] == page.date)`.
- **LOGIC-05 & 06 (Pre-scan and Routing):** Implement `verified_residents` set population right after Pass 1.5. Use this set during the Pass 2 loop to implement D-05 (Temporary Routing). Use a `prefix_buffer` to implement D-06 (Retrospective Assignment).

---

## Validation Architecture

To ensure the new grouping and timeline logic functions correctly without running expensive and slow LLM calls, a robust testing strategy focused purely on Pass 2 (the grouping logic) is required by the Nyquist validation gate.

### 1. Testing Framework & Strategy
- **Framework:** `pytest`
- **Focus:** Test the timeline iteration loop in `src/pipeline.py` (Pass 2) by mocking the output of Pass 1 (the `raw_pages` list of `PageClassification` models).
- **Isolation:** By providing deterministic, hardcoded `PageClassification` objects, we can strictly validate state transitions, buffering, and document grouping.

### 2. Test Paths & Scenarios
- **`test_logic_01_large_family`:** Mock an Anchor document with 8 resident names. Assert it successfully establishes a new timeline instead of being skipped/falling back to UNKNOWN.
- **`test_logic_02_array_order`:** Mock an Anchor document where the 1st name is a new spouse, but the 2nd name matches the `current_primary_tenant`. Assert the timeline does NOT split and stays assigned to the family.
- **`test_logic_03_single_word_names`:** Mock a timeline with a single-word tenant name ("محمد") and a subsequent Anchor document with the same single-word name. Assert they group correctly despite the small word count.
- **`test_logic_04_date_grouping`:** Mock two consecutive pages of the same category with *different* dates. 
  - *Subtest A:* `is_continuation=False` -> Assert it produces 2 separate `DocumentGroup` objects.
  - *Subtest B:* `is_continuation=True` -> Assert it merges them into 1 `DocumentGroup`.
- **`test_logic_05_prefix_rescue`:** Mock an early non-anchor (e.g., `PERSONAL_DETAILS`) at page 1, followed by an Anchor document at page 2. Assert the page 1 document is retrospectively assigned to the Anchor's tenant instead of being permanently orphaned. Include a test where *no* anchor is ever found, asserting the buffer flushes to `UNKNOWN` at the end.
- **`test_logic_06_non_anchor_routing`:** Mock a pre-scan scenario where "Ahmad" and "Khalid" are established as verified residents via Anchor docs. Then mock a Notification for "Khalid" (assert routes to Khalid) and a Notification for "RandomName" (assert ignores "RandomName" and defaults to `current_primary_tenant`).

### 3. Execution & Integration
- Create `tests/test_timeline_logic.py`.
- Refactor Pass 2 of `process_pdf` into a standalone method (`_group_pages_into_documents(self, raw_pages, canonical_mapping)`) to make it callable from unit tests without triggering the PyMuPDF or GemmaClient pipelines.
