# Cross-AI Plan Review Request
You are reviewing implementation plans for a software project phase.
Provide structured feedback on plan quality, completeness, and risks.

## Project Context
# Arabic Housing Document Categorizer

## What This Is

An automated document processing application that takes scanned Arabic housing files (often up to 200 pages long), extracts their text via multimodal vision, and processes them using the Gemma 4 31b model. It organizes the disorganized input into a deeply structured directory hierarchy, categorizing pages into smaller PDF files by house number, chronological residents, and 13 specific document types, while intelligently keeping multi-page letters intact.

## Core Value

Accurately parsing, splitting, and categorizing large, disorganized scanned Arabic documents into an exact 13-category chronological folder structure without losing the context of multi-page topics.

## Requirements

### Validated

- ✓ Implement robust Arabic OCR pipeline for scanned PDFs and images (replaced by direct LLM vision) — Phase 01
- ✓ Integrate with the Gemma 4 31b model via the user's specific API/hosting setup for document understanding — Phase 01
- ✓ Detect page continuations so multi-page letters on the same topic stay in a single combined PDF — Phase 01
- ✓ Implement PDF splitting logic to extract specific pages into smaller PDF files — Phase 01

### Active

- ✓ Extract the House Number to create the root directory (e.g., `683`) — v1.0
- ✓ Extract Resident information, double-sort them, and organize chronologically — v1.0
- ✓ Handle structural edge cases: "Amar Takhsees" and generic house-related letters — v1.0
- ✓ Generate 13 distinct subfolders per person — v1.0
- ✓ Build a desktop GUI to wrap the CLI logic — v1.0

### Active

- [ ] Implement robust retry logic to handle 429 and 500 API errors — v1.1
- [ ] Optimize the speed vs. accuracy tradeoff for processing long documents — v1.1
- [ ] Improve the accuracy of the final generated house files — v1.1

### Out of Scope

- [Saving text only] — We must split the original file into smaller PDF files to retain visual integrity, not just save text.
- [Using default large context models like Gemini 1.5 Pro natively] — User explicitly requested to route processing through Gemma 4 31b.

## Current State

Shipped **v1.0 MVP**. The core pipeline now correctly processes Arabic documents via Gemma 4 31b, resolves primary tenants across continuous pages, and generates the required chronological 13-category folder structure. A `Tkinter` desktop GUI was built to make it easy to select PDFs and output directories.

## Current Milestone: v1.2 Core Stabilization & Logic Overhaul

**Goal:** Fix the 19 critical structural, OS, and logic bugs identified in the deep dives to ensure absolute stability, correct Arabic timeline sorting, and prevent data corruption.

**Target features:**
- OS, File I/O, and GUI Issues: Compress PDFs before processing, fix cache IO bottlenecks, atomic saves, rmtree wipes, PyMuPDF locks, OS path crashes, and GUI freezing.
- LLM, Schema, and Prompt Issues: Remove house_number from prompts, prevent Entity Resolver from erasing family members, and fix silent LLM retries.
- Timeline, Arabic Logic, and Output Structure: Fix date-mismatch fusing, non-anchor routing, empty folders, zero-pad sorting, the `.replace` Arabic string mutilation, orphaned prefix documents, and large family/array-order timeline hijacking.

## Context

- The input housing documents are scanned Arabic files, highly disorganized, and can contain 200+ pages.
- Resident details are not always sorted chronologically in the input file; double sorting is required (first by who lived there and who didn't, then chronologically).
- Some letters relate to the house itself and not a specific person.
- The model must perform complex NLP categorization on OCR'd Arabic text to determine the specific document type out of the 13 categories.

## Constraints

- **Language and Formatting**: Arabic OCR — Scanned Arabic text can be difficult to extract accurately, which is a prerequisite for the LLM to categorize the pages.
- **Model Choice**: Gemma 4 31b — The application must use this specific model, relying on the user's API setup.
- **Document Integrity**: Page Continuation — Continuations of letters must be kept together in a single PDF file and not split arbitrarily page-by-page.
- **Output Format**: PDF Extraction — The final categorized files must be smaller PDFs sliced from the original PDF.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use Gemma 4 31b | User explicitly requested this specific model over alternatives | Verified in Phase 01 |
| Split PDFs | Extracting smaller PDFs retains the original visual integrity of the documents rather than just raw text | Verified in Phase 01 |
| Multimodal Vision over traditional OCR | Gemma-4-31b handles Arabic scans natively, skipping a fragile secondary OCR step | Verified in Phase 01 |
| Exact Arabic Name Matching | User requested strict exact Arabic name intersection without smart normalization | Stops name mutilation (Phase 05) |
| Image-based Blank Page Heuristics | Use file size (<15KB) instead of PDF text extraction | Prevent LLM token waste on blank scans (Phase 05) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):


## Phase 6: Core Grouping & Timeline Logic
### Requirements Addressed
# Milestone v1.2 Requirements

This document tracks the active requirements and goals for Milestone v1.2: Core Stabilization & Logic Overhaul.

## Category 1: OS, File I/O, and GUI Stability (IO)

- [ ] **IO-01 (Atomic Cache Saving):** The system must save the `.cache.json` file atomically (write to a temporary file, then rename) to prevent the entire cache from being corrupted or truncated to 0 bytes if the application is forcibly closed, crashes, or loses power during the write operation.
- [ ] **IO-02 (PDF Compression & Preservation):** The system must still copy the full original PDF into the house directory as requested. However, before processing and copying, it must compress the PDF to significantly reduce the massive file sizes, saving disk space without losing the full context file.
- [ ] **IO-03 (File Lock Release):** The `PdfIngestor` must explicitly call `doc.close()` on the PyMuPDF document after iterating through it, preventing the OS from holding a permanent file lock on the PDF (which currently blocks users from moving or deleting the file in Windows).
- [ ] **IO-04 (OS Path Sanitization):** The `_sanitize_filename` function must strip control characters like `\n` and `\r` from resident names. Currently, if the AI hallucinates a line break in a name, `os.makedirs` will violently crash the application when attempting to create an illegal Windows path.
- [ ] **IO-05 (GUI Telemetry Optimization):** The `poll_telemetry` function must be optimized to only render the most recent state in the Treeview instead of redundantly deleting and re-inserting hundreds of queued intermediate states. This prevents the severe UI freezing and flickering currently happening under heavy processing loads.
- [ ] **IO-06 (Safe Directory Overwrites):** The system must safely merge new output into existing house directories rather than using `shutil.rmtree` to destructively wipe out the entire folder (and all its contents) every time a new processing run occurs on the same house number.
- [ ] **IO-07 (Cache Validation Safety):** The system must wrap the cache loading logic in proper exception handling (e.g., `try/except ValidationError`) to safely handle outdated or manually modified cache files, preventing the entire pipeline from instantly crashing upon startup.

## Category 2: Core Timeline and Document Grouping Logic (LOGIC)

- [ ] **LOGIC-01 (Family Size Resilience):** The pipeline must allow Anchor documents (like Housing Contracts or Basic Details forms) containing more than 3 names to establish a new timeline. Currently, the `len(valid_mapped) <= 3` limit causes large families to be ignored and their documents orphaned to the "UNKNOWN" folder.
- [ ] **LOGIC-02 (Array Order Independence):** When an Anchor document lists multiple names (e.g., Husband and Wife), the grouping logic must correctly match the family to the current timeline regardless of which name the AI happened to output first in the array. Currently, it only checks `valid_mapped[0]`, causing immediate timeline hijacking if the spouse is listed first.
- [ ] **LOGIC-03 (Accurate Name Matching):** The word intersection math (`< 2` threshold) must be adjusted to correctly handle valid single-word Arabic names (e.g., "محمد"). Currently, single-word names mathematically cannot share 2 words, forcing them into duplicate, fragmented resident folders.
- [ ] **LOGIC-04 (Precise Date Grouping):** The pipeline must stop merging documents together indiscriminately. It must enforce strict date-matching during the grouping phase so that consecutive pages with different dates are recognized as separate documents.
- [ ] **LOGIC-05 (Prefix Document Rescue):** ID Cards (`PERSONAL_DETAILS`) and other non-anchor documents that appear at the very beginning of a scanned dossier must be able to initialize the timeline or be safely held until a timeline is established. Currently, because they aren't Anchor documents, they are permanently orphaned to the fallback folder.
- [ ] **LOGIC-06 (Non-Anchor Recipient Routing):** Non-anchor documents (like specific notifications or EWA letters) must respect the recipient name extracted by the AI. Currently, they are blindly forced into the `current_primary_tenant`'s folder even if the AI explicitly stated the letter belongs to a different family member.

## Category 3: Arabic Data Integrity and Output Formatting (ARABIC)

- [ ] **ARABIC-01 (Arabic String Safety):** The system must remove the destructive `.replace("ال", "")` logic. This crude string manipulation carves letters out of the middle of legitimate Arabic names (e.g., destroying "خالد" into "خاد"), causing random timeline splits and corrupt folder names.
- [ ] **ARABIC-02 (Zero-Padded Folder Sorting):** The 13 Arabic output folders must be zero-padded (e.g., `01. `, `02. `) instead of starting with raw numbers. Because Windows File Explorer uses lexicographical sorting, the current folders visually display out of chronological order (e.g., `1, 10, 11, 2, 3`), ruining the narrative flow.
- [ ] **ARABIC-03 (Dynamic Folder Generation):** The system must only generate Arabic category subfolders dynamically when a file actually needs to be written to them. Currently, it hardcodes the creation of all 13 empty folders for every single resident, creating massive visual clutter.

## Category 4: LLM Error Handling and Entity Resolution (LLM)

- [ ] **LLM-01 (Identity Preservation):** The `resolve_entities` LLM prompt in Pass 1.5 must correctly map and retain non-primary family member identities (like wives and children). Currently, it aggressively maps everyone to the primary tenant, permanently erasing their distinct identities from the output.
- [ ] **LLM-02 (Reliable Retries):** The pipeline must stop silently swallowing LLM extraction errors with bare `except Exception: pass` blocks. All exceptions must be caught, logged, and trigger the robust 429/500 retry logic instead of falling back to default/missing data.
- [ ] **LLM-03 (Other Letters Catch-All Fix):** The `other_letters` category must be removed from `NONE_EXPECTED_CATEGORIES`. This forces the pipeline to actively retry when the AI lazily dumps documents into `other_letters` without extracting any names, rather than blindly accepting the incomplete extraction.

## Future Requirements
None yet defined.

## Out of Scope
- **Saving Text Only:** The user requires the original visual format of the PDFs to be retained (via extraction and compression), rather than simply outputting raw OCR text.
- **Switching Models:** Gemma 4 31b remains the core model; no migration to Gemini 1.5 Pro natively.


### User Decisions (CONTEXT.md)
# Phase 6: Core Grouping & Timeline Logic - Context

**Gathered:** 2026-06-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Overhaul the logic that groups pages into documents and assigns them to resident timelines, ensuring families stay together and documents aren't orphaned or hijacked.

</domain>

<decisions>
## Implementation Decisions

### Large families on Anchor docs (LOGIC-01)
- **D-01:** Keep a safety threshold of 10 names for anchor documents to prevent massive parsing errors from hijacking timelines.

### Date mismatch grouping (LOGIC-04)
- **D-02:** Add an `is_continuation` boolean flag to the LLM extraction schema (Pass 1). The grouping logic will respect this flag to merge undated or mismatching pages that are continuations. 
- **D-03:** The LLM extraction and retry logic for `is_continuation` MUST respect the global rate limits and backoff logic to prevent hammering the API.

### Prefix ID cards (LOGIC-05) & Non-Anchor routing (LOGIC-06)
- **D-04:** Implement **"Verified Residents" Pre-scan:** Before Pass 2 groups any documents, scan all pages for Anchor documents (Contracts, Basic Details, Key Handover). Any name on an Anchor document is officially registered as a Verified Resident.
- **D-05:** Implement **Temporary Routing:** For non-anchor documents (e.g. Notifications), route the document to the named person ONLY if they are a Verified Resident. Otherwise, ignore the unverified name and leave the document in the current active timeline.
- **D-06:** Implement **Retrospective Assignment:** Buffer any early non-anchor documents (like Prefix ID cards) encountered while the timeline is still `UNKNOWN`. When the first Anchor document is found and establishes a timeline, retroactively assign the buffered documents to that newly verified resident.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 6 success criteria
- `.planning/REQUIREMENTS.md` — LOGIC-01 through LOGIC-06 details

### Code Structure
- `src/pipeline.py` — Location of the 2-pass architecture and timeline logic that needs updating
- `src/organizer.py` — Location of `_build_resident_order` and folder generation rules
- `src/schemas.py` — Where `is_continuation` flag will be added

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/schemas.py` defines the `PageClassification` schema that needs extending.
- `pipeline.py` Pass 1.5 (`canonical_mapping`) runs over the whole file before Pass 2. This allows the Verified Residents Pre-scan to be done right after Pass 1.5.

### Established Patterns
- Pass 1 processes pages via ThreadPoolExecutor. Retries for `is_continuation` missing must reuse `self.client.classify_page` error handling to respect the 15 RPM cap.
- Pass 2 iterates sequentially over `raw_pages`.

### Integration Points
- Temporary Routing will replace lines 198-202 in `pipeline.py`.
- Retrospective Assignment will require adding a buffer queue before the main loop starts assigning `documents.append()`.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 6-Core Grouping & Timeline Logic*
*Context gathered: 2026-06-23*


### Research Findings
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


### Plans to Review
---
wave: 1
depends_on: []
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

```yaml
must_haves:
  truths:
    - (D-01) Anchor documents with up to 10 names establish timelines.
    - Anchor documents preserve the timeline if any named person matches the current tenant.
    - Single-word Arabic names correctly overlap and match without failing the intersection threshold.
    - [D-02] Documents only group if `date` matches exactly OR `is_continuation` is True.
    - D-03: The LLM extraction and retry logic for is_continuation MUST respect rate limits.
    - Implement Verified Residents Pre-scan D-04.
    - ID cards at the front of a file are buffered and retroactively assigned to the first anchor's tenant (D-06).
    - Non-anchor letters only assign to named residents if they are Verified Residents [D-05].
```

## Tasks

```xml
<task>
  <read_first>
    <file>src/schemas.py</file>
    <file>src/pipeline.py</file>
  </read_first>
  <action>
    Add `is_continuation: bool = Field(default=False, description="True if this page is a continuation of the previous page, False otherwise")` to `PageClassification` in `src/schemas.py`.
    In `src/pipeline.py::process_single_page`, wrap `self.client.classify_page` in a `for attempt in range(3):` retry loop. If `InvalidResponseError` or `LLMFailureError` occurs, sleep using exponential backoff (e.g. `time.sleep(2 ** attempt)`) and retry. Only fallback to `Category.OTHER_LETTERS` and `UNKNOWN` resident if all 3 attempts fail.
  </action>
  <acceptance_criteria>
    `PageClassification` schema accepts and defaults `is_continuation`.
    `process_single_page` successfully retries up to 3 times on `InvalidResponseError` and `LLMFailureError` before executing the fallback block.
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
    Implement Prefix Document Rescue: initialize `prefix_buffer: list[DocumentGroup] = []` for documents parsed while `current_primary_tenant == "UNKNOWN"`. When `current_primary_tenant` changes from "UNKNOWN" to a valid name, iterate over `prefix_buffer`, update their `primary_tenant`, and extend `documents`. If the loop finishes and timeline is still UNKNOWN, flush `prefix_buffer` to `documents` as UNKNOWN.
  </action>
  <acceptance_criteria>
    `verified_residents` set correctly aggregates anchor names before Pass 2 loop.
    `prefix_buffer` safely holds early pages and retroactively applies the `primary_tenant` once an anchor establishes the timeline.
    `prefix_buffer` correctly flushes as UNKNOWN if no anchor is ever found.
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
    3. If document is NOT an anchor, use `page_primary_tenant = valid_mapped[0]` ONLY IF `valid_mapped[0] in verified_residents`. Otherwise fallback to `current_primary_tenant`.
    4. Modify the group merge condition to: `documents[-1].dates[-1] == page.date or page.is_continuation`.
  </action>
  <acceptance_criteria>
    Matching conditional successfully checks up to 10 names.
    Single-word names match correctly via `min(2, len(), len())` dynamic threshold.
    Array order does not hijack if a subsequent name matches the current tenant.
    Non-anchor pages correctly fallback to the current tenant if the candidate name is unverified.
    Consecutive pages merge if dates match or `is_continuation` is True.
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


## Review Instructions
Analyze each plan and provide:
1. **Summary** � One-paragraph assessment
2. **Strengths** � What's well-designed (bullet points)
3. **Concerns** � Potential issues, gaps, risks (bullet points with severity: HIGH/MEDIUM/LOW)
4. **Suggestions** � Specific improvements (bullet points)
5. **Risk Assessment** � Overall risk level (LOW/MEDIUM/HIGH) with justification

Output your review in markdown format.
