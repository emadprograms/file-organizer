# Phase 2: Pass 1 — Document Cleaning - Research

## 1. Domain & Scope
**Goal:** Process the input JSON report to ensure every single page has a canonical tenant name and a resolved date before moving on to document grouping and routing.
**Boundary:** This phase is strictly about *data resolution and cleaning*. It parses the input JSON, processes the metadata, and outputs a clean, fully-resolved state for the next phase. No PDF splitting or file writing happens here.

## 2. Requirements Mapping
We must address requirements **CLN-01** through **CLN-10**:
*   **Data Models (CLN-01):** Parse the raw JSON into structured `PageData` Pydantic models containing `category`, `content_explanation`, `expected_tenant_name`, `date`, `sender`, `receiver`, and `subject`.
*   **Anchor Identification (CLN-02):** Filter pages to find "anchor" documents: `contract`, `forms`, `id_cards`. Extract expected tenant names from these.
*   **Canonicalization (CLN-03):** Merge spelling/OCR variations of tenant names. Approach (D-01):
    1. Arabic text normalization (strip diacritics, unify alef/yeh/teh marbuta).
    2. `RapidFuzz` for obvious string similarity merges.
    3. `LLMClient` with structured output for transliteration gaps and hard errors.
*   **Qualification (CLN-04):** Primary tenants must appear on $\ge$ 1 anchor document AND $\ge$ 5 total documents after canonicalization. Discard all others.
*   **Timeline Building (CLN-05):** Build tenant timelines from absolute `min` and `max` dates of assigned documents for each qualified tenant.
*   **Date Inference (CLN-06):** Fill `null` dates inferring from nearest dated page by index proximity (D-02: tie-breaking by looking backward).
*   **Page Assignment (CLN-07, CLN-08, CLN-09):**
    *   Assign each page to the tenant whose timeline covers the page's date (CLN-07).
    *   Overlap periods $\rightarrow$ earlier tenant wins (CLN-07).
    *   Unresolvable pages fall into an "Unassigned (YYYY-MM)" bucket based on their inferred date (CLN-08, D-03).
    *   Exactly one expected_tenant_name per page (no ambiguity) (CLN-09).
*   **Final State Validation (CLN-10):** Every page has a canonical tenant name and a resolved date (except Unassigned).

## 3. Existing Code & Dependencies
*   **`src/organize.py`**: CLI structure, environment validation, logging, and `LLMClient` initialization is present.
*   **`src/llm_client.py`**: Handles retries, rate limits (7s), and Google GenAI instantiation. Use `generate_content` for the LLM translation step.
*   **Tech Stack Rules:** `pydantic` for models, `rapidfuzz` for fuzzy matching, and stdlib `json`/`re`/`unicodedata` for text prep. 
*   **Integration Points:** Will need to add parsing logic to `src/organize.py` (or delegate to a new module like `src/cleaning.py`) directly after `LLMClient` initialization.

## 4. Execution Plan Strategy
To plan this phase effectively, the implementation should be structured sequentially:
1.  **Define Models:** Create `PageData` and `Tenant` Pydantic models.
2.  **Load & Parse:** Read the JSON report and instantiate `PageData` objects.
3.  **Date Resolution:** First pass to standardize date formats and fill `null` dates using the index proximity algorithm (tie-break backward).
4.  **Tenant Extraction & Normalization:** Extract names. Apply Arabic normalization and RapidFuzz to group similar names.
5.  **LLM Canonicalization:** Send clustered/hard-to-resolve names to the LLM (via `LLMClient`) to get a final mapping dictionary.
6.  **Timeline Generation:** Filter out unqualified tenants, calculate `min`/`max` active dates for the remaining ones.
7.  **Final Assignment:** Iterate through all pages and assign them to a canonical tenant or the "Unassigned" bucket based on timeline bounds.

## 5. Key Considerations & Edge Cases
*   **Arabic Normalization:** RapidFuzz is exact-character based. Standardizing characters (e.g., `أ`/`إ`/`آ` $\rightarrow$ `ا`) is critical *before* calculating similarity scores.
*   **Date Formats:** The JSON report might have inconsistent date strings. We need a robust date parsing utility to compare and infer dates correctly.
*   **LLM Prompting:** The canonicalization prompt needs to clearly instruct the LLM to output a JSON mapping. Use Pydantic schemas in `google-genai` for structured generation if supported, or enforce JSON formatting strictly.
*   **Statelessness:** The output of this phase should be a clean list of `PageData` objects, ready for Phase 3 document grouping. We should consider returning this state cleanly or temporarily saving it.

## Validation Architecture
*   **Input Validation:** Assert the loaded JSON matches the `PageData` schema using Pydantic.
*   **Canonicalization Assertions:** Verify the LLM response maintains all keys sent to it (no dropped names).
*   **Timeline Integrity:** Check that `min_date <= max_date` for all generated tenant timelines.
*   **Post-Condition Checks (CLN-10):** 
    *   Assert exactly zero pages have a `null` expected_tenant_name (must be a valid tenant or 'Unassigned').
    *   Assert exactly zero pages have a `null` date.
*   **Reconciliation:** Verify the number of parsed `PageData` objects matches the array length in the raw JSON file.
