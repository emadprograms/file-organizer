# Debug Session: Name Identification and Page Grouping Failures

## Issue Description
During Phase 2 UAT, two major issues were identified:
1. **Name Identification:** Gemma inconsistently extracts Arabic names (which can have 4-5 parts, sometimes written in English or Arabic). More critically, it frequently returns `NONE` for the resident name when a name actually exists on the document.
2. **Page Grouping:** Pages that belong to the same topic (e.g., pages 30-32 which are all "Basic Details") are incorrectly separated into different document groups rather than being merged via `is_continuation`.

## Root Cause Analysis

### 1. Name Identification
- **System Prompt Weakness:** The system prompt briefly mentions normalizing names but does not give explicit instructions to capture all 4-5 parts of an Arabic name if present, nor does it instruct the LLM on handling English vs. Arabic names robustly.
- **Lack of Retry Logic for `NONE`:** The LLM sometimes misses the name due to OCR noise or complex layouts and defaults to `NONE`. The pipeline currently accepts `NONE` blindly (except for `amar_takhsees` where it is expected). There is no programmatic retry mechanism to double-check if the name is truly missing.

### 2. Page Grouping (Sliding Window Bug)
- **State Leakage/Omission:** In `src/pipeline.py`, the `previous_summary` is only updated when a document group is *closed* and emitted. 
- When evaluating if Page 31 is a continuation of Page 30, the `previous_summary` passed to the LLM describes Page 29 (the last closed group). 
- The LLM is completely blind to the fact that Page 30 was just classified as "Basic Details". Because it has no context about the *currently active* group, it cannot reliably flag Page 31 as `is_continuation: true`, leading it to start a new group.

## Proposed Fixes

1. **Robustify Name Extraction & Retry Logic:**
   - Update `_build_system_prompt` in `src/llm.py` to explicitly instruct Gemma to extract the full 4-5 part Arabic name, checking both Arabic and English text.
   - Implement a retry loop inside `classify_page` in `src/llm.py`: if the result returns `resident="NONE"`, and the category is not one where `NONE` is explicitly expected (like `amar_takhsees`), explicitly retry the LLM call once or twice with an appended prompt like "Are you sure there is no name? Please look closely."

2. **Fix Sliding Window Context (Active Group Awareness):**
   - In `src/pipeline.py`, pass BOTH `previous_closed_summary` AND `active_group_summary` to `classify_page`.
   - Update `classify_page` to include the active group in the prompt (e.g., "Currently processing a document starting at page X with category Y. Is this page a continuation of that document?").
   - Update `pipeline.py` to keep track of the `active_group_summary` dynamically as pages are added to it.
