---
wave: 1
depends_on: []
files_modified:
  - src/cleaning.py
  - src/organize.py
autonomous: true
---

# Phase 2: Pass 1 — Document Cleaning

## Goal
Implement the document cleaning pipeline: parse the JSON report, resolve canonical tenant names using anchors, infer missing dates, and assign every page to a canonical tenant or the "Unassigned" bucket.

## Requirements Covered
- CLN-01, CLN-02, CLN-03, CLN-04, CLN-05, CLN-06, CLN-07, CLN-08, CLN-09, CLN-10

## Security Threat Model
<threat_model>
- **ASVS Level:** 1
- **Blocking Threshold:** high
- **Mitigations:** 
  - Ensure JSON parsing strictly enforces schema via Pydantic to prevent arbitrary data injection.
  - Apply filesystem-safe sanitization implicitly (or ensure it's tracked for Phase 4) though we only deal with internal state here.
  - Rate limits are preserved in the LLMClient calls to prevent DOS against the upstream API.
</threat_model>

## Verification Criteria
- All `PageData` objects output by the pipeline have `resolved_date` != null and `canonical_tenant` != null.
- Unresolvable pages are mapped to a tenant starting with `Unassigned (`.
- `python src/organize.py <valid_dir>` runs the cleaning phase and reports success.

## Must Haves
- Pydantic models for `PageData`.
- Date inference logic based on absolute index distance.
- Arabic string normalization and RapidFuzz clustering.
- Integration with `LLMClient` for canonicalization.

## Artifacts this phase produces
- `src/cleaning.py`: New module for document cleaning.
- `PageData`: Pydantic model class for page-level data.
- `TenantTimeline`: Pydantic model class for timeline bounds.
- `load_and_parse_json`: Function to load JSON to models.
- `infer_missing_dates`: Function to fill null dates.
- `normalize_arabic_text`: Function for string normalization.
- `cluster_names_fuzzily`: Function to cluster names using RapidFuzz.
- `canonicalize_with_llm`: Function using LLM to map remaining names.
- `build_tenant_timelines`: Function to qualify tenants and build timelines.
- `assign_pages_to_tenants`: Function to map pages to timelines.
- `process_cleaning_phase`: Main coordinator function.
- CLI argument updates: `src/organize.py` modified to call `process_cleaning_phase`.

## Tasks

<task>
  <action>
    Create test infrastructure: `tests/conftest.py` and `tests/test_cleaning.py`.
    - `conftest.py` should define shared pytest fixtures for `PageData` and `TenantTimeline` mock data.
    - `test_cleaning.py` should contain initial test stubs for the cleaning module logic.
  </action>
  <read_first>
    - .planning/phases/02-pass-1-document-cleaning/02-VALIDATION.md
  </read_first>
  <acceptance_criteria>
    - `pytest tests/` runs successfully.
  </acceptance_criteria>
</task>

<task>
  <action>
    Create `src/cleaning.py` and define Pydantic models `PageData` and `TenantTimeline`.
    - `PageData`: fields `category` (str), `content_explanation` (str), `expected_tenant_name` (Optional[str]), `date` (Optional[str]), `sender` (str), `receiver` (str), `subject` (str). Add computed fields `canonical_tenant` (Optional[str] initialized to None), `resolved_date` (Optional[str] initialized to None), and `original_index` (int).
    - `TenantTimeline`: fields `canonical_name` (str), `min_date` (str), `max_date` (str).
    Implement `load_and_parse_json(json_path: Path) -> list[PageData]` to load the raw JSON, add `original_index` starting from 0, and return instantiated models.
    - Assert that the number of instantiated `PageData` objects matches the array length in the original raw JSON file.
  </action>
  <read_first>
    - src/cleaning.py
    - .planning/phases/02-pass-1-document-cleaning/02-RESEARCH.md
  </read_first>
  <acceptance_criteria>
    - `python -c "from src.cleaning import PageData, TenantTimeline, load_and_parse_json"` executes successfully.
    - `PageData` instantiated from a valid dict does not raise ValidationError.
    - Loading JSON verifies the list length matches the source array.
  </acceptance_criteria>
</task>

<task>
  <action>
    Implement `infer_missing_dates(pages: list[PageData]) -> None` in `src/cleaning.py`.
    - For each page where `date` is None, find the nearest page (by `original_index` distance) where `date` is not None.
    - If distances are equal, pick the page with the smaller `original_index` (backward tie-break).
    - Set the `resolved_date` on all pages to either their own `date` or the inferred date.
  </action>
  <read_first>
    - src/cleaning.py
    - .planning/phases/02-pass-1-document-cleaning/02-CONTEXT.md
  </read_first>
  <acceptance_criteria>
    - Given a list of pages with dates `["2020-01-01", None, None, "2020-01-05"]`, `infer_missing_dates` resolves them to `["2020-01-01", "2020-01-01", "2020-01-05", "2020-01-05"]`.
  </acceptance_criteria>
</task>

<task>
  <action>
    Implement `normalize_arabic_text(text: str) -> str` and `cluster_names_fuzzily(names: set[str]) -> dict[str, str]` in `src/cleaning.py`.
    - `normalize_arabic_text` must strip diacritics, convert أ/إ/آ to ا, convert ة to ه, and convert ى to ي using regex and `unicodedata.normalize('NFKC', text)`.
    - `cluster_names_fuzzily` must use `rapidfuzz.fuzz.ratio` with a threshold of 85 to group similar normalized names. It returns a mapping from the original name to the longest string in its cluster (as a temporary canonical representative).
  </action>
  <read_first>
    - src/cleaning.py
  </read_first>
  <acceptance_criteria>
    - `python -c "from src.cleaning import normalize_arabic_text; assert normalize_arabic_text('أحمد') == 'احمد'"` succeeds.
    - `python -c "from src.cleaning import cluster_names_fuzzily; res = cluster_names_fuzzily({'محمد علي', 'محمد على'}); assert len(set(res.values())) == 1"` succeeds.
  </acceptance_criteria>
</task>

<task>
  <action>
    Implement `canonicalize_with_llm(unresolved_names: list[str], llm_client: LLMClient) -> dict[str, str]` in `src/cleaning.py`.
    - Use `llm_client.generate_content` with a JSON-formatted prompt asking to map the provided names to unified canonical identities (merging transliterations/OCR errors).
    - IMPORTANT: Explicitly instruct the LLM to output all canonical identities strictly in **Arabic**.
    - The `config` must enforce `response_mime_type="application/json"`.
    - Parse the response text as a JSON dictionary.
    - Assert that the returned dictionary contains all keys from the `unresolved_names` list (ensuring no names were dropped from the mapping) and return it.
  </action>
  <read_first>
    - src/cleaning.py
    - src/llm_client.py
    - .planning/phases/02-pass-1-document-cleaning/02-PATTERNS.md
  </read_first>
  <acceptance_criteria>
    - Source assertion: `canonicalize_with_llm` calls `llm_client.generate_content` with `response_mime_type="application/json"` and explicitly requires Arabic outputs.
    - Source assertion: Verifies response dictionary keys exactly match the input list before returning.
  </acceptance_criteria>
</task>

<task>
  <action>
    Implement `build_tenant_timelines(pages: list[PageData], canonical_mapping: dict[str, str]) -> list[TenantTimeline]` in `src/cleaning.py`.
    - Identify anchors (category is one of: `contract`, `forms`, `id_cards`).
    - Apply `canonical_mapping` to `expected_tenant_name` to get a provisional canonical name.
    - Qualify tenants: A canonical name is qualified if it appears on >=1 anchor page AND >=5 total pages.
    - For each qualified tenant, calculate `min_date` and `max_date` based on the `resolved_date` of all pages assigned to them.
    - Assert that `min_date <= max_date` for all generated `TenantTimeline` objects.
    - Return a list of `TenantTimeline` objects.
  </action>
  <read_first>
    - src/cleaning.py
    - .planning/REQUIREMENTS.md
  </read_first>
  <acceptance_criteria>
    - Behavior assertion: Unqualified tenants (no anchors or <5 total pages) are dropped and do not get a `TenantTimeline`.
    - Behavior assertion: `min_date` and `max_date` accurately reflect the string bounds (YYYY-MM-DD) of the pages belonging to the tenant.
    - Source assertion: Asserts `min_date <= max_date` before returning timelines.
  </acceptance_criteria>
</task>

<task>
  <action>
    Implement `assign_pages_to_tenants(pages: list[PageData], timelines: list[TenantTimeline]) -> None` in `src/cleaning.py`.
    - For each page, compare `resolved_date` against all `TenantTimeline` objects.
    - Assign `canonical_tenant` to the timeline whose range covers `resolved_date`. If multiple cover it, pick the timeline with the earliest `min_date` (earliest tenant wins).
    - If no timeline covers the date, assign `canonical_tenant` to `f"Unassigned ({page.resolved_date[:7]})"` (e.g., Unassigned (2020-05)).
    - If `resolved_date` is None for some reason, assign `Unassigned (Unknown)`.
    - Ensure EVERY page has exactly one `canonical_tenant`.
  </action>
  <read_first>
    - src/cleaning.py
    - .planning/REQUIREMENTS.md
  </read_first>
  <acceptance_criteria>
    - Behavior assertion: Pages falling in overlapping timeline periods are assigned to the tenant with the older timeline.
    - Behavior assertion: Pages falling outside all timelines get `Unassigned (YYYY-MM)` based on their `resolved_date`.
  </acceptance_criteria>
</task>

<task>
  <action>
    Implement `process_cleaning_phase(json_path: Path, llm_client: LLMClient) -> list[PageData]` in `src/cleaning.py` to coordinate all previous tasks.
    - Load JSON, infer dates.
    - Extract all unique `expected_tenant_name`s (ignoring Nones).
    - Fuzzy cluster the names, then send the unique representatives to `canonicalize_with_llm` to get a final `raw -> canonical` mapping.
    - Build timelines and assign pages.
    - Assert that no page has `canonical_tenant == None` or `resolved_date == None`.
    - Return the fully resolved list of `PageData` objects.
  </action>
  <read_first>
    - src/cleaning.py
  </read_first>
  <acceptance_criteria>
    - Source assertion: `process_cleaning_phase` uses `assert` to verify that no page has `canonical_tenant == None` or `resolved_date == None` before returning.
  </acceptance_criteria>
</task>

<task>
  <action>
    Integrate `process_cleaning_phase` into `src/organize.py`.
    - Import `process_cleaning_phase` from `src.cleaning`.
    - In `main()`, locate the JSON file using `list(args.target_dir.glob("*_report.json"))[0]`.
    - Call `cleaned_pages = process_cleaning_phase(json_path, llm_client)`.
    - Log the number of pages cleaned successfully and the number of unique tenants resolved.
  </action>
  <read_first>
    - src/organize.py
    - src/cleaning.py
    - .planning/phases/02-pass-1-document-cleaning/02-PATTERNS.md
  </read_first>
  <acceptance_criteria>
    - Source assertion: `organize.py` imports and calls `process_cleaning_phase` correctly.
  </acceptance_criteria>
</task>
