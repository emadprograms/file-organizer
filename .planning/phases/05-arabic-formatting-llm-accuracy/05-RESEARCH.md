# Phase 05 Research: Arabic Formatting & LLM Accuracy

## 1. Context & Patterns Identified
The pipeline classifies and organizes documents in three main stages: ingestion/classification (`llm.py`), grouping/timeline resolution (`pipeline.py`), and file writing (`organizer.py`). 
We identified the following patterns related to this phase's requirements:
- **Destructive String Mutation**: `pipeline.py` uses `.replace("ال", "")` during timeline word intersection, aggressively carving letters from valid names.
- **Eager Folder Allocation**: `organizer.py` pre-emptively allocates all 13 empty category directories for every verified resident in "Phase B", leading to massive filesystem clutter.
- **Error Swallowing vs Pipeline Crashing**: Currently, `llm.py` silently swallows json parsing/LLM errors after 2 retries (falling back to generic data), while `pipeline.py` violently crashes the entire `ThreadPoolExecutor` if a hard exception escapes the LLM layer.

## 2. Files to Modify & Technical Approach

### `src/pipeline.py`
- **ARABIC-01 (Arabic String Safety)**: Remove `.replace("ال", "")` inside `process_pdf` (around line 153). Replace with exact whitespace splitting `set(current_primary_tenant.split())`.
- **LLM-02 (Retry Limits & Fallback)**: In `process_single_page`, catch `Exception` instead of raising it to shut down the executor. Log the failure and return a fallback `PageClassification(house_number="UNKNOWN", residents=["UNKNOWN"], category=Category.OTHER_LETTERS, date="NONE")`. This safely isolates the failure and allows the rest of the pipeline to continue processing.

### `src/organizer.py`
- **ARABIC-02 (Zero-Padded Folder Sorting)**: Update the `CATEGORY_FOLDERS` dictionary keys 1-9 to be zero-padded (`01_`, `02_`, etc.) to ensure lexicographical OS sorting.
- **ARABIC-03 (Dynamic Folder Generation)**: Remove the loop in `organize()` that eager-creates `CATEGORY_FOLDERS.values()` for every resident. Move the directory creation JIT (just-in-time) inside "Phase C" right before `extract_pdf_segment` is called: `os.makedirs(target_dir, exist_ok=True)`.
- **Fallback Folder Logic**: Ensure that documents with tenant "UNKNOWN" route properly to an `UNKNOWN` fallback directory in Phase C, rather than just lumping them into generic house letters.

### `src/llm.py`
- **LLM-01 (Identity Preservation)**: Rewrite the `resolve_entities` system prompt (around line 478) to explicitly instruct the LLM to retain non-primary family member identities instead of merging them. Remove the rule that forces mapping family to the Primary Tenant's name.
- **LLM-02 (Reliable Retries)**: Remove the silent error swallowing block (`if invalid_retries >= 2: return PageClassification...`) in `classify_page` (around line 443). Allow exceptions to trigger the existing `if is_invalid` retry mechanism and eventually bubble up as `LLMFailureError` so the pipeline layer can handle the fallback routing properly.
- **LLM-03 (Other Letters Catch-All Fix)**: Remove `'other_letters'` from the `NONE_EXPECTED_CATEGORIES` set.

## 3. Potential Risks
- **Excessive Retries on Garbage Pages**: Removing `other_letters` from `NONE_EXPECTED_CATEGORIES` means the LLM will actively retry if it can't find a name on a literal blank or purely unreadable page. We rely on the `max_attempts` circuit breaker to prevent infinite loops.

## Validation Architecture

To satisfy NYQUIST constraints, the QA agent must verify this implementation using the following architecture:

**Test Boundaries:**
- The changes strictly span `organizer.py` (filesystem generation), `pipeline.py` (timeline math and error bounds), and `llm.py` (prompting and retry triggers).

**Data Setup:**
1. **Organizer Test**: Mock a list of `DocumentGroup` objects that only contain documents for Category 1 and Category 5.
2. **Pipeline Fallback Test**: Inject a mock `GemmaClient` that unconditionally raises `LLMFailureError("Simulated LLM crash")` on a specific page.
3. **Pipeline Intersection Test**: Send two identical names with different spacing/prefixes but without "ال" stripping required.

**Required Assertions:**
1. **Dynamic Formatting (ARABIC-02/03)**: Assert that `os.path.exists()` is `True` ONLY for `01_البيانات الاساسية` and `05_عقد الانتفاع`. Assert that `02_` through `13_` were NEVER created. Assert the folders are properly zero-padded.
2. **Resilient Fallback (LLM-02)**: Assert that the pipeline completes `process_pdf` without crashing the thread pool, and that the returned document list contains an entry mapped to the `UNKNOWN` resident.
3. **Strict Math (ARABIC-01)**: Assert that the `.replace("ال", "")` is completely absent from `pipeline.py` logic.
4. **Retry Threshold (LLM-03)**: Assert `Category.OTHER_LETTERS.value` is not in `GemmaClient.NONE_EXPECTED_CATEGORIES`.
