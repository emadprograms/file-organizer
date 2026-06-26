# Phase 08: Technical Debt Clearance & Code Hardening
**Objective:** Perform code audit, remove dead code/redundant logic, implement type safety (strict type hints, `mypy` enforcement), add Pydantic validation, and sync docstrings.

## Execution Summary
1. **Dead Code Elimination & Consolidation:**
   - Consolidated `_extract_text_with_qwen` into `extract_page` in `src/llm.py`, reducing redundant logic paths and standardizing the interface.
   - Consolidated `_classify_text_with_local_model` into `classify_extracted_page` in `src/llm.py`, resolving duplicated vision-to-text pathing logic.
   - Removed unused/inline imports across `src/llm.py` and `src/organizer.py`.
   - Removed duplicate `return documents` blocks in `src/organizer.py`.

2. **Type Safety & Hardening:**
   - Added missing type annotations (e.g., `Optional`, `Dict`, `Tuple`, `List`, `Set`) to all methods in `src/organizer.py`.
   - Corrected return types, variable type inferences (`Optional[Exception]`), and missing imports for `mypy` in `src/llm.py` and `src/pipeline.py`.
   - Enforced Pydantic validation on all unstructured JSON fallbacks and confirmed `response_format` schemas correctly utilized `pydantic.BaseModel`.

3. **Code Quality Checks:**
   - Added docstrings to consolidated LLM methods.
   - Passed `mypy` type checks for the updated data boundaries.

The implementation is complete and successfully resolves the cloud API rate-limiting fallbacks without generating unused dead code.
