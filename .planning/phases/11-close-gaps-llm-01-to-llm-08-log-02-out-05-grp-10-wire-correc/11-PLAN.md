---
wave: 1
depends_on: []
files_modified:
  - src/logger.py
  - src/llm_client.py
  - src/processing/grouping.py
  - src/processing/routing.py
  - src/processing/organizer.py
autonomous: true
---

# Plan 11: Close Gaps (LLM, LOG, OUT, GRP)

## Requirements
- LLM-01: Centralized LLM client — all calls routed through single class
- LLM-08: Other LLM call 500s: skip item after 5 consecutive, log warning
- LOG-02: Full audit trail: every LLM call, grouping decision, routing decision, tenant resolution
- OUT-05: Create "Unassigned" folder with inferred period in name
- GRP-10: Multi-match routing via LLM, must return JSON with `folder` and `reason`

## Verification
- `must_haves`:
  - `truths`:
    - `src/processing/grouping.py` contains `llm_client.generate_content(` instead of `_route_llm_call`.
    - `src/processing/routing.py` contains `llm_client.generate_content(` instead of `_route_llm_call`.
    - `src/logger.py` contains `def log_decision_trace(`.
    - `RoutingResponse` in `src/processing/routing.py` has `reason: str`.
    - Unassigned folder naming format `Unassigned ({min_ym} to {max_ym})` is present in `src/processing/organizer.py`.
    - Audit trace JSONs are written for grouping, routing, and tenant resolution via `log_decision_trace`.
  - `prohibitions`:
    - `grouping.py` must NOT use `_route_llm_call`.
    - `routing.py` must NOT use `_route_llm_call`.

## Artifacts this phase produces
- `src.logger.log_decision_trace`
- `src.processing.routing.RoutingResponse.reason`
- Updated `src.llm_client.LLMClient.generate_content` signature

## Tasks

<task>
  <id>1</id>
  <title>Update Logger for Audit Tracing (LOG-02)</title>
  <description>Add utility in `src/logger.py` to write structured JSON audit logs for pipeline decisions.</description>
  <read_first>
    - src/logger.py
  </read_first>
  <action>
    - Add `def log_decision_trace(decision_type: str, payload: dict, run_id: str = None):` to `src/logger.py`.
    - Retrieve `log_dir` via `_run_directories.get(run_id)` or fallback to generating one using the current timestamp (similar to `log_llm_api_call`).
    - Create `traces` subdirectory inside `log_dir` if it doesn't exist.
    - Save the `payload` JSON to `{log_dir}/traces/{timestamp}_{decision_type}.json` with `ensure_ascii=False` and `indent=2`.
  </action>
  <acceptance_criteria>
    - `src/logger.py` contains `def log_decision_trace(decision_type: str, payload: dict, run_id: str = None)`.
    - JSON is written to `traces/` with `ensure_ascii=False`.
  </acceptance_criteria>
</task>

<task>
  <id>2</id>
  <title>Update LLMClient to Support Schema Output & Boundary Chunk Shrinking</title>
  <description>Update `generate_content` in `src/llm_client.py` to accept Pydantic models and properly raise an exception on boundary call errors to force prompt shrinking.</description>
  <read_first>
    - src/llm_client.py
  </read_first>
  <action>
    - Define a new exception `LLMChunkShrinkRequiredError(LLMClientError)` in `src/llm_client.py`.
    - Import `types` from `google.genai`.
    - Modify `generate_content` to accept `response_schema: type | None = None`. (Remove `on_shrink_chunk`).
    - If `response_schema` is provided, pass `config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=response_schema)` as a kwarg into `self.client.models.generate_content`.
    - Return `response.parsed` if `response_schema` was provided (this contains the parsed Pydantic object), otherwise return the raw `response`.
    - Keep local variables `consecutive_429` and `consecutive_500` inside `generate_content` to inherently satisfy "Error counters reset on ANY successful response".
    - Update the 500 error handling: if `is_boundary_call=True` and `consecutive_500 >= 5`, immediately raise `LLMChunkShrinkRequiredError`. For non-boundary calls, skip the item (return `None`) and log a warning after 5 errors.
  </action>
  <acceptance_criteria>
    - `generate_content` accepts `response_schema` and removes `on_shrink_chunk`.
    - `types.GenerateContentConfig` is instantiated and passed to `generate_content` when `response_schema` is present.
    - `response.parsed` is returned when a schema is present.
    - `LLMChunkShrinkRequiredError` is defined and raised at 5 consecutive 500s when `is_boundary_call=True`.
  </acceptance_criteria>
</task>

<task>
  <id>3</id>
  <title>Update Semantic Routing Logic & Schema (GRP-10)</title>
  <description>Force LLM to produce a reasoning step before routing and switch to new LLMClient.</description>
  <read_first>
    - src/processing/routing.py
    - src/logger.py
  </read_first>
  <action>
    - Add `reason: str = Field(description="Explanation of why this folder was selected")` to `RoutingResponse`.
    - Update `prompt_template` in `route_document` to explicitly ask the LLM to explain why the document fits into the selected folder based on the summary.
    - Change `_route_llm_call` to `generate_content` from `llm_client`. Pass `response_schema=RoutingResponse`.
    - If `generate_content` returns `None` (which means it skipped due to 500 errors), fallback to `13_others`.
    - Record the routing decision by logging an inline summary using `log.info(...)` and saving a trace via `log_decision_trace("routing", {"category": category, "selected": selected, "reason": ...})`.
  </action>
  <acceptance_criteria>
    - `RoutingResponse` contains `reason: str`.
    - `_route_llm_call` is removed from `routing.py`.
    - `log_decision_trace("routing", ...)` is called.
  </acceptance_criteria>
</task>

<task>
  <id>4</id>
  <title>Refactor Grouping to use New LLMClient and Handle Shrink Exception</title>
  <description>Switch from the old `llm.py` client to `llm_client.py` in `grouping.py`, handle chunk shrink exceptions, and log decisions.</description>
  <read_first>
    - src/processing/grouping.py
    - src/logger.py
  </read_first>
  <action>
    - Change `_route_llm_call` to `generate_content` in `process_with_shrink`. Pass `response_schema=GroupingResponse`, `is_boundary_call=True`.
    - Import and catch `LLMChunkShrinkRequiredError` from `src.llm_client`.
    - If `LLMChunkShrinkRequiredError` is caught, immediately trigger a chunk shrink (increment `chunk_size_idx` if possible, reset `consecutive_failures`) so the next loop iteration rebuilds the prompt with a smaller chunk size.
    - For other exceptions (e.g. Validation errors), continue incrementing `consecutive_failures` and shrinking if it hits `MAX_CONSECUTIVE_FAILURES`.
    - After successfully computing `final_groups`, loop over them or log once at the end using `log_decision_trace("grouping", {"chunk_groups": ...})` and `log.info(...)` for inline summary.
  </action>
  <acceptance_criteria>
    - `_route_llm_call` is removed from `grouping.py`.
    - `llm_client.generate_content` is called with `is_boundary_call=True`.
    - `LLMChunkShrinkRequiredError` is caught and immediately shrinks the chunk.
    - `log_decision_trace("grouping", ...)` is invoked.
  </acceptance_criteria>
</task>

<task>
  <id>5</id>
  <title>Update Unassigned Period Naming & Tenant Tracing (OUT-05)</title>
  <description>Format unassigned folders using inferred YYYY-MM periods and log tenant resolution.</description>
  <read_first>
    - src/processing/organizer.py
    - src/logger.py
  </read_first>
  <action>
    - In `FileOrganizer.organize`, modify the `tenant_years` extraction loop:
      - If `group_tenant == "Unassigned"`, use `re.search(r'(\d{4}-\d{2})', d.strip())` to extract the `YYYY-MM` prefix instead of just `YYYY`. If extracted, add it to `tenant_years[group_tenant]`.
      - For normal tenants, continue using `re.search(r'(\d{4})', d.strip())`.
    - In the folder naming loop, if `tenant == "Unassigned"`, build the folder name as `Unassigned ({min_ym} to {max_ym})` (or `غير مخصص ({min_ym} to {max_ym})` for Arabic consistency).
    - At the end of folder mapping, log the decisions via `log_decision_trace("tenant_resolution", {"tenant_folders": tenant_folder_names})` and `log.info(...)` for the inline summary.
  </action>
  <acceptance_criteria>
    - Regex `r'(\d{4}-\d{2})'` is used for "Unassigned".
    - `Unassigned` folder uses `{min_ym} to {max_ym}` format.
    - `log_decision_trace("tenant_resolution", ...)` is called.
  </acceptance_criteria>
</task>
