---
wave: 1
depends_on: []
files_modified:
  - src/pipeline.py
  - src/organizer.py
  - src/llm.py
  - .planning/ROADMAP.md
autonomous: true
---

# Phase 05 Plan: Arabic Formatting & LLM Accuracy

## Goal
Stop the pipeline from actively mutilating Arabic names, ensure output folders sort correctly, and force the LLM to preserve family identities instead of swallowing errors.

## requirements
- ARABIC-01
- ARABIC-02
- ARABIC-03
- LLM-01
- LLM-02
- LLM-03

## must_haves
1. The 13 category folders must be zero-padded (e.g., `01_`, `02_`) for correct lexicographical sorting.
2. Category folders must only be created dynamically just-in-time when a file is saved (no pre-allocation of all 13 folders).
3. The `.replace("ال", "")` logic must be completely removed from timeline word intersection.
4. Non-primary family member identities (like wives and children) must be preserved in entity resolution, not mapped to the primary tenant.
5. Exceptions during LLM parsing must trigger the formal retry loop, and specific exceptions like `LLMFailureError` must be caught for fallback instead of broad `Exception`s.
6. Fallback classifications must preserve the `house_number` if known.
7. `other_letters` must be removed from `NONE_EXPECTED_CATEGORIES` so missing names trigger a retry, with a pre-check to avoid wasting retries on blank pages.
8. The blank page pre-check must use image-based heuristics (like pixmap variance) instead of text extraction, since the PDFs are scans and text extraction will falsely flag all pages as blank.

## Artifacts this phase produces
- No new persistent standalone artifacts are produced; purely codebase mutations.

## Review Incorporations & Rejections
- **Review finding regarding Task 1 (Arabic string matching)**: The reviewer expressed a HIGH concern that exact string intersection for Arabic names will fail on common "ال" variations and suggested a smart normalizer. **Decision**: Explicitly REJECTED. As per `05-CONTEXT.md`, the user decided to disable stripping entirely and rely strictly on exact matches and native LLM normalization.
- **Review finding regarding Task 6 (Blank page detection)**: The reviewer expressed a HIGH concern that using PyMuPDF `get_text()` on scanned pages will falsely flag them all as blank. **Decision**: ACCEPTED. Task 6 has been updated to require image-based heuristics instead of text extraction.
- **Review finding regarding Task 5 (Fallback and Exception swallowing)**: Reviewer noted these were HIGH concerns but partially resolved by the current plan. **Decision**: ACCEPTED. We will proceed with Task 5 as planned to fully resolve them.

## tasks

<task>
<id>1</id>
<title>ARABIC-01: Remove Destructive Arabic String Mutation</title>
<description>Remove the `.replace("ال", "")` logic during timeline word intersection to stop carving letters out of valid names. Note: Review suggestion to implement smart normalizers is rejected based on user decision to rely strictly on exact matches.</description>
<action>Modify `process_pdf` in `src/pipeline.py` to remove `.replace("ال", "")`. Replace with exact whitespace splitting `set(current_primary_tenant.split())`.</action>
<read_first>
- src/pipeline.py
</read_first>
<acceptance_criteria>
- The `.replace("ال", "")` string method is entirely removed from the timeline intersection logic in `src/pipeline.py`.
</acceptance_criteria>
</task>

<task>
<id>2</id>
<title>ARABIC-02: Zero-Padded Folder Sorting and Roadmap Update</title>
<description>Update the Arabic output folders to use zero-padding and underscore formatting for correct Windows lexicographical sorting, and update the Roadmap to reflect this decision.</description>
<action>Modify `CATEGORY_FOLDERS` in `src/organizer.py` to zero-pad keys 1-9 (`01_`, `02_`, etc.) and ensure they use underscore separators (e.g., `01_البيانات الاساسية`). Also, update ARABIC-02 success criteria in `.planning/ROADMAP.md` to show `01_` instead of `01. `.</action>
<read_first>
- src/organizer.py
- .planning/ROADMAP.md
</read_first>
<acceptance_criteria>
- `CATEGORY_FOLDERS` keys in `src/organizer.py` start with a zero-padded number followed by an underscore for all categories.
- ARABIC-02 success criteria in `.planning/ROADMAP.md` reflects the `01_` format instead of `01. `.
</acceptance_criteria>
</task>

<task>
<id>3</id>
<title>ARABIC-03: Dynamic Folder Generation & Fallback Routing</title>
<description>Prevent pre-emptive creation of empty category folders. Create them dynamically when writing a PDF.</description>
<action>Remove the eager folder allocation loop in `organize()` in `src/organizer.py`. Move `os.makedirs(target_dir, exist_ok=True)` into "Phase C" right before `extract_pdf_segment` is called. Ensure documents with tenant "UNKNOWN" route properly to an `UNKNOWN` fallback directory.</action>
<read_first>
- src/organizer.py
</read_first>
<acceptance_criteria>
- No loop eagerly creating `CATEGORY_FOLDERS.values()` for every resident.
- `os.makedirs` is called just-in-time in "Phase C" before `extract_pdf_segment`.
- Fallback routing explicitly handles the `UNKNOWN` resident.
</acceptance_criteria>
</task>

<task>
<id>4</id>
<title>LLM-01: Preserve Distinct Family Identities</title>
<description>Rewrite the system prompt for entity resolution so non-primary family members retain their distinct identities.</description>
<action>Update the `resolve_entities` system prompt in `src/llm.py` to explicitly instruct the LLM to retain non-primary family member identities instead of merging them to the Primary Tenant's name.</action>
<read_first>
- src/llm.py
</read_first>
<acceptance_criteria>
- `resolve_entities` prompt instructs LLM to retain distinct identities for wives and children instead of replacing them with the primary tenant name.
</acceptance_criteria>
</task>

<task>
<id>5</id>
<title>LLM-02: Reliable Retries & Safe Fallback for Exceptions</title>
<description>Stop silently swallowing exceptions in the LLM layer, catch specific validation errors without masking structural bugs, and preserve context during fallback.</description>
<action>In `src/llm.py`, remove the silent error swallowing `if invalid_retries >= 2: return PageClassification...` inside `classify_page` to let exceptions trigger the retry mechanism. In `src/pipeline.py`'s `process_single_page`, catch `LLMFailureError` (and any other specific expected extraction errors) instead of a broad `Exception`. On fallback, preserve the `house_number` from the current batch/context if available instead of hardcoding "UNKNOWN". Set `residents=["UNKNOWN"]`.</action>
<read_first>
- src/llm.py
- src/pipeline.py
</read_first>
<acceptance_criteria>
- `src/llm.py` does not swallow exceptions on invalid parsing, allowing the retry loop to throw `LLMFailureError`.
- `process_single_page` in `src/pipeline.py` catches `LLMFailureError` (not a broad `Exception`).
- Fallback logic in `process_single_page` assigns the `house_number` context from the batch if it was already known.
</acceptance_criteria>
</task>

<task>
<id>6</id>
<title>LLM-03: Enforce Retries for Missing Names in Other Letters</title>
<description>Force the pipeline to actively retry when documents are dumped into other_letters without names, while explicitly managing blank pages to avoid wasting retries.</description>
<action>Remove `'other_letters'` from the `NONE_EXPECTED_CATEGORIES` set in `src/llm.py`. Implement a pre-check before sending pages to the LLM to identify completely blank/empty pages. This pre-check MUST use image analysis (e.g., checking for high variance/non-white pixels on the PyMuPDF pixmap or file size thresholds) rather than text extraction, since the PDFs are scans.</action>
<read_first>
- src/llm.py
</read_first>
<acceptance_criteria>
- `Category.OTHER_LETTERS.value` (or `'other_letters'`) is no longer in `NONE_EXPECTED_CATEGORIES` in `src/llm.py`.
- A mechanism exists to pre-check for completely blank pages before triggering LLM calls.
- The blank page pre-check uses image variance or pixel analysis, not text extraction.
</acceptance_criteria>
</task>
