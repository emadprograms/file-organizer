---
phase: 3
reviewers: [gemini, antigravity]
reviewed_at: 2026-07-04T16:45:00+03:00
plans_reviewed:
  - 01-PLAN.md
  - 02-PLAN.md
  - 03-PLAN.md
  - 04-PLAN.md
  - 05-PLAN.md
  - 06-PLAN.md
---

# Cross-AI Plan Review — Phase 3

## Gemini Review

### Summary
The proposed plans for Phase 3 are exceptionally well-structured, exhibiting a clear linear dependency chain (Wave 1 → Wave 6) that logically builds from data definitions to core algorithms, LLM orchestration, routing logic, and finally system integration. The strategy directly addresses every requirement (GRP-01 through GRP-13) and incorporates the specific user decisions regarding overlap resolution (D-01) and resilient failure recovery (D-03). The transition from the current "declarative" grouping to an LLM-driven boundary detection system is handled surgically, minimizing risk by isolating logic in new modules (`grouping.py`, `routing.py`) before wiring them into the `Pipeline`.

### Strengths
- **Resilient Error Handling:** The `process_with_shrink` mechanism (Plan 3) is a robust implementation of the requirement to handle 500 errors by reducing context window size (10 → 5 → 3), preventing total pipeline failure on complex chunks.
- **Separation of Concerns:** Moving routing logic from `FileOrganizer` (where it currently resides in a basic declarative form) to a dedicated `src/processing/routing.py` (Plan 4) allows for cleaner testing of the 13-folder logic independent of filesystem IO.
- **Verification-First Approach:** Plan 1 and Plan 2 prioritize the creation of unit tests for the "pure-Python" grouping algorithms (`verify_groups`, `merge_chunks`) before introducing the non-deterministic LLM layer.
- **Consistent LLM Pattern:** The use of `_route_llm_call` with Pydantic schemas in `LLMClient` (Plan 3 & 4) maintains architectural consistency with the existing `classify_page_direct` implementation.

### Concerns

| Severity | Concern | Evidence / Mechanism |
| :--- | :--- | :--- |
| **LOW** | `DocumentGroup` Type Mutation | `src/core/schemas.py:15` defines `DocumentGroup` as a `@dataclass`. Plan 1 proposes extending it with `reason`, `brief_arabic_title`, and `folder_path`. While simple, mixing `@dataclass` with optional Pydantic-like fields in a project heavily using `BaseModel` elsewhere could lead to inconsistency. |
| **LOW** | PDF Page Indexing Ambiguity | `src/processing/split.py:34` uses `dst_doc.insert_pdf(src_doc, from_page=start_page, to_page=end_page)`, which is 0-indexed and inclusive. The plans refer to `start_page` and `end_page` throughout. If any logic in `grouping.py` accidentally introduces 1-based indexing or exclusive ranges, it will cause off-by-one errors in the final PDFs. |
| **MEDIUM** | LLM Prompting for Boundaries | GRP-03 requires boundaries **ONLY** on subject/content shift (ignoring date/sender). LLMs often struggle with "negative constraints" (do NOT use X). If the prompt is not rigorously tuned, the LLM may still split on date changes, violating the core requirement. |

### Suggestions
- **Schema Alignment:** Convert `DocumentGroup` from a `@dataclass` to a Pydantic `BaseModel` in Plan 1. This ensures consistency with `UserConfig` and other schemas, and provides better validation for the new `folder_path` and `reason` fields.
- **Prompt Engineering:** In Plan 3, include a "Few-Shot" example in the grouping prompt specifically showing a date change that **should NOT** result in a boundary, and a subject change that **SHOULD**. This will mitigate the risk identified in the "Concerns" section.
- **Boundary Edge Case Test:** Add a specific test case to `tests/test_grouping.py` where a document spans exactly across a chunk boundary (e.g., starts at page 9, ends at page 11) to verify that `merge_chunks` correctly handles the overlap page (Page 10).

### Risk Assessment
**Overall Risk: LOW**

The design is conservative and highly disciplined. By implementing the "pure" grouping logic first and wrapping it in a resilient shrink-loop, the team has mitigated the primary risks associated with LLM instability and context window limits. The plan's adherence to the established `LLMClient` routing pattern ensures that cloud failover and rate-limiting (7s delay) remain intact. The primary remaining risk is prompt-level adherence to boundary rules, which is an iterative tuning task rather than an architectural flaw.

---

## Antigravity Review

### Summary

The plans correctly identify the necessary steps to transition the pipeline into a boundary-detection LLM grouping approach with semantic routing. They effectively leverage the existing `_route_llm_call` for schema validation and retry logic, and they map well to the existing two-pass architecture. However, there are significant gaps in how the `process_with_shrink` handles iteration state upon failure, how the organizer identifies single-match documents for file naming, and how the changes integrate with the existing configuration-driven strategy patterns in `pipeline.py`.

### Strengths

*   **Leverages existing LLM infrastructure:** Plan 3 correctly plans to use `_route_llm_call` in `src/llm/llm.py:87`, which already supports the `response_schema` parameter and handles Pydantic validation flawlessly without needing to reinvent extraction logic.
*   **Fits existing data models:** Plan 1 correctly targets `src/core/schemas.py:13` to extend the `DocumentGroup` dataclass, ensuring downstream compatibility. Because `dates` is a `list[str]`, appending optional fields to the dataclass is safe.
*   **Reuses PDF splitting logic:** Plan 5 correctly integrates with the existing `extract_pdf_segment` function used in `src/processing/organizer.py:105`, avoiding duplicate PDF manipulation logic.

### Concerns

| Severity | Concern | Evidence / Mechanism |
| :--- | :--- | :--- |
| **HIGH** | `process_with_shrink` Iteration State | `process_with_shrink` shrinks the chunk size on failure (10→5→3). However, `generate_chunks` is described in Plan 2 as a sliding window generator. A static generator won't allow dynamic resizing mid-iteration. The sliding window must be recalculated from the failure point, but the plan doesn't specify how this state is managed. |
| **MEDIUM** | Single-Match Filename State Gap | Plan 5 requires `FileOrganizer.organize` to format filenames as `YYYY-MM-DD.pdf` for single-match docs. Plan 1 doesn't add a mechanism to `DocumentGroup` to flag a document as single-match. Without this explicit signal, `organizer.py` won't know when to omit the `{brief_arabic_title}`. |
| **MEDIUM** | Bypassing Strategy Pattern | Plan 6 completely hardcodes the grouping logic into the pipeline (`pipeline.py:490`), bypassing the configuration-driven `grouping_cfg.strategy` switch (`pipeline.py:460`). This violates the architecture unless implemented as a specific configurable strategy. |
| **LOW** | Organizer Architectural Mismatch | Routing logic (`determine_folder`) is moved to `pipeline.py` (Plan 6). Currently, routing is handled in `FileOrganizer`. Shifting this leaves `FileOrganizer` solely as a file writer despite it receiving `config` in its signature, creating a slight mismatch. |

### Suggestions

*   In Plan 2/3, implement the grouping loop with a while-loop managing an explicit `current_page_index` rather than a static generator for `generate_chunks`. This allows the chunk size to shrink dynamically for the remaining pages without losing the iteration position.
*   In Plan 1, add an `is_direct_routed: bool = False` (or similar) field to `DocumentGroup` in `src/core/schemas.py` so `FileOrganizer` (Plan 5) explicitly knows when to use the date-only `YYYY-MM-DD.pdf` filename format.
*   In Plan 6, instead of blindly removing the declarative grouping block, wrap the new LLM boundary grouping under a new strategy check (e.g., `if config.grouping.strategy == "llm_boundary":`) to maintain the configuration-driven architecture.
*   Ensure Plan 3 relies on `_route_llm_call`'s existing 429/cooldown logic and only uses the `process_with_shrink` fallback specifically for validation failures or 500 server errors, to prevent double-implementing rate limit backoffs.

### Risk Assessment
**Overall Risk: MEDIUM**

The architectural direction is sound and maps beautifully to the existing codebase, particularly the LLM client. However, the logical gap in handling dynamic chunk resizing during iteration (Plan 3) will cause runtime bugs, and the data-passing gap for direct-routed filenames (Plan 5) will fail the naming requirements. The suggestions provided resolve these risks easily.

---

## Consensus Summary

Both Gemini and Antigravity validated the overall architecture and reuse of existing LLM client patterns, but they caught distinct and highly actionable architectural and logic flaws. Antigravity focused heavily on runtime state and structural design, while Gemini focused on prompt engineering and schema correctness.

### Agreed Strengths
- **Resilient Error Handling:** The chunk-shrink circuit breaker is a solid design for handling 500s.
- **Consistent LLM Usage:** Both praised the reuse of `_route_llm_call` and existing Pydantic validation infrastructure.
- **Separation of Concerns:** Moving routing out to a dedicated module allows for cleaner testing.

### Agreed Concerns
1. **HIGH — `process_with_shrink` Iteration State (Antigravity):** A static generator (`generate_chunks`) cannot dynamically resize mid-iteration. The loop needs to explicitly track `current_page_index` to handle dynamic shrinking.
2. **MEDIUM — Strategy Pattern Bypass (Antigravity):** Hardcoding the new logic in `pipeline.py` breaks the existing `grouping_cfg.strategy` switch. It should be implemented as a new strategy (e.g., `"llm_boundary"`).
3. **MEDIUM — LLM Boundary Prompt Risk (Gemini):** The LLM may ignore negative constraints ("don't split on date changes"). Few-shot examples are required in the prompt.
4. **MEDIUM — Single-Match Filename Gap (Antigravity):** `FileOrganizer` won't know when to drop the `{brief_arabic_title}` without an explicit flag on `DocumentGroup` (e.g., `is_direct_routed: bool`).
5. **LOW — Schema Consistency (Gemini):** `DocumentGroup` should be a Pydantic `BaseModel` instead of a `@dataclass` to align with the rest of the project and validate new fields.
6. **LOW — Page Indexing Ambiguity (Gemini):** Clear 0-indexed bounds must be verified against PyMuPDF requirements.

### Divergent Views
The two systems evaluated entirely different problem spaces. Gemini reviewed the external API/Prompt surface and schema typing. Antigravity reviewed the algorithmic execution state (sliding window) and internal architecture patterns (strategy configurations). They are complementary, making the combined plan significantly stronger.
