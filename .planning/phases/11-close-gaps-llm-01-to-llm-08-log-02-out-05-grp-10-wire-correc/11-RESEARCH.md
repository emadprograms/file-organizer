# Phase 11 Research: Close Gaps (LLM, LOG, OUT, GRP)

## Objective
Identify how to implement the missing requirements for LLM Client error handling, audit logging, unassigned folder naming, and semantic routing to finalize the v1.0 milestone.

## 1. LLMClient Error Handling (LLM-01 to LLM-08)
**Current State:**
- The codebase currently has two LLM clients: `src/llm/llm.py` and `src/llm_client.py`.
- `src/llm_client.py` implements the strict logic described in the requirements (400/404 fail fast, 500 wait 15s retry, 429 wait 65s retry, and boundary detection chunk shrinking).
- However, `grouping.py` and `routing.py` currently import and use `src/llm/llm.py` via `_route_llm_call`.

**Implementation Plan:**
- Unify the client usage to ensure LLM-01 to LLM-08 are respected. This means refactoring `grouping.py` and `routing.py` to use `src/llm_client.py` instead of `src/llm/llm.py`, and updating `src/llm_client.py` to accept structured JSON schema extraction natively (by passing the `response_schema` directly to `generate_content` via the `google-genai` SDK configuration).
- Ensure that the error counter reset on success (LLM-09) is appropriately implemented inside `src/llm_client.py`.

## 2. Audit Logging (LOG-02)
**Current State:**
- `src/logger.py` handles writing LLM API calls to `llm_audit.jsonl`.
- There is some trace writing logic buried inside `src/llm/llm.py` for successful and failed calls.

**Implementation Plan:**
- Per D-01, implement decision logging (grouping, routing, tenant resolution) both as inline summaries in `app.log` (via `logging.getLogger().info`) and as detailed JSON in `logs/traces/` for structural analysis.
- Add utility functions in `src/logger.py` (e.g., `log_decision_trace(decision_type, payload)`) to standardize writing the JSON files into the `traces/` subdirectory for any decision event.

## 3. Unassigned Period Naming (OUT-05)
**Current State:**
- `src/processing/organizer.py` (lines 41-77) aggregates `min_year` and `max_year` for all tenants by matching `(\d{4})` from dates.
- It then formats the unassigned folder name as `غير مخصص (فترة مستنتجة) {min_year}-{max_year}`.

**Implementation Plan:**
- Per D-02, the unassigned folder must use the format: `Unassigned (YYYY-MM to YYYY-MM)`.
- Modify `tenant_years` aggregation in `organizer.py` to extract and track `YYYY-MM` periods (using regex `(\d{4}-\d{2})`) exclusively for the "Unassigned" tenant, while retaining `YYYY` for normal tenants.
- Update the folder name construction loop to generate `Unassigned ({min_ym} to {max_ym})` when the tenant is Unassigned.

## 4. Semantic Routing Response (GRP-10)
**Current State:**
- `src/processing/routing.py` defines `RoutingResponse` as a Pydantic `BaseModel` with a single field: `selected_folder: str`.
- `route_document()` calls the LLM with this schema when a category belongs to `MULTI_MATCH`.

**Implementation Plan:**
- Per D-03, add a `reason: str = Field(...)` to `RoutingResponse` so the LLM is forced to generate a reasoning step before selecting the folder.
- Update the `prompt_template` in `route_document` to explicitly ask the LLM to explain why the document fits into the selected folder based on the summary.
- The `google-genai` client inherently maps Pydantic models to JSON schema when passed to `response_schema`, fulfilling the requirement of how to pass the JSON schema to the Gemini API.
