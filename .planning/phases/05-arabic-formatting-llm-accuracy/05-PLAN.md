---
wave: 1
depends_on: []
files_modified:
  - src/pipeline.py
  - src/organizer.py
  - src/llm.py
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
5. All exceptions during LLM parsing must trigger the formal retry loop instead of being silently swallowed.
6. `other_letters` must be removed from `NONE_EXPECTED_CATEGORIES` so missing names trigger a retry.

## Artifacts this phase produces
- No new persistent standalone artifacts are produced; purely codebase mutations.

## tasks

<task>
<id>1</id>
<title>ARABIC-01: Remove Destructive Arabic String Mutation</title>
<description>Remove the `.replace("ال", "")` logic during timeline word intersection to stop carving letters out of valid names.</description>
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
<title>ARABIC-02: Zero-Padded Folder Sorting</title>
<description>Update the Arabic output folders to use zero-padding and underscore formatting for correct Windows lexicographical sorting.</description>
<action>Modify `CATEGORY_FOLDERS` in `src/organizer.py` to zero-pad keys 1-9 (`01_`, `02_`, etc.) and ensure they use underscore separators (e.g., `01_البيانات الاساسية`).</action>
<read_first>
- src/organizer.py
</read_first>
<acceptance_criteria>
- `CATEGORY_FOLDERS` keys in `src/organizer.py` start with a zero-padded number followed by an underscore for all categories.
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
<title>LLM-02: Reliable Retries & Fallback for Exceptions</title>
<description>Stop silently swallowing exceptions in the LLM layer, route them to fallback logic instead of crashing the pipeline.</description>
<action>In `src/llm.py`, remove the silent error swallowing `if invalid_retries >= 2: return PageClassification...` inside `classify_page` to let exceptions trigger the retry mechanism. In `src/pipeline.py`'s `process_single_page`, catch `Exception`, log it, and return a fallback `PageClassification` mapped to "UNKNOWN".</action>
<read_first>
- src/llm.py
- src/pipeline.py
</read_first>
<acceptance_criteria>
- `src/llm.py` does not swallow exceptions on invalid parsing, allowing the retry loop to throw `LLMFailureError`.
- `process_single_page` in `src/pipeline.py` catches `Exception` and returns an UNKNOWN `PageClassification` fallback.
</acceptance_criteria>
</task>

<task>
<id>6</id>
<title>LLM-03: Enforce Retries for Missing Names in Other Letters</title>
<description>Force the pipeline to actively retry when documents are dumped into other_letters without names.</description>
<action>Remove `'other_letters'` from the `NONE_EXPECTED_CATEGORIES` set in `src/llm.py`.</action>
<read_first>
- src/llm.py
</read_first>
<acceptance_criteria>
- `Category.OTHER_LETTERS.value` (or `'other_letters'`) is no longer in `NONE_EXPECTED_CATEGORIES` in `src/llm.py`.
</acceptance_criteria>
</task>
