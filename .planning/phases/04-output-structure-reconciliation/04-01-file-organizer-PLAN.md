---
phase: 04-output-structure-reconciliation
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/processing/organizer.py
  - tests/test_organizer.py
autonomous: true
requirements: [OUT-01, OUT-02, OUT-03, OUT-04, OUT-05, OUT-06, LOG-04, DIFF-03]
must_haves:
  truths:
    - PDF segments are written to dynamic tenant and topic folders
    - Topic folders are created on-demand only
    - A detailed JSON manifest of the page mapping is written to disk
    - The pipeline halts if total input pages do not match total output pages
  artifacts:
    - src/processing/organizer.py
    - tests/test_organizer.py
  key_links:
    - extract_pdf_segment in organizer.py

## Artifacts this phase produces
- `src/processing/organizer.py:FileOrganizer` (modified class)
- `src/processing/organizer.py:run_reconciliation` (new function)
- `output/{house_id}_manifest.json` (new file output)
---

<objective>
Rewrite FileOrganizer to build the final output directory hierarchy per user constraints, handle Unassigned folders, create topic subdirectories on demand, and implement the reconciliation logic.

Purpose: Translate the logical document grouping from Pass 2 into the final physical filesystem structure and guarantee page conservation.
Output: Refactored FileOrganizer class and run_reconciliation function.
</objective>

<execution_context>
@.agents/gsd-core/workflows/execute-plan.md
@.agents/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/04-output-structure-reconciliation/04-CONTEXT.md
@.planning/phases/04-output-structure-reconciliation/04-RESEARCH.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Rewrite FileOrganizer core & routing</name>
  <files>src/processing/organizer.py, tests/test_organizer.py</files>
  <read_first>
    - src/processing/organizer.py
    - src/processing/pipeline.py
    - src/core/schemas.py
  </read_first>
  <action>
    Rewrite `FileOrganizer` to maintain the `output_dir` parameter and pass `house_id` for use in the manifest/reconciliation step (addressing Base Directory Context Loss). 
    Perform an initial aggregation pass across all `documents` to compute the `(min_year, max_year)` for every unique `primary_tenant` based on `dates` list. 
    Intercept `primary_tenant` strings starting with "Unassigned", strip the month suffix, and group them as the singular "Unassigned" tenant for date aggregation.
    Implement tenant directory naming: `{canonical_arabic_name} {year_start}-{year_end}/`. 
    Implement Unassigned directory naming: `غير محدد {year_start}-{year_end}/`, with fallback to exactly `غير محدد/` if all dates are null (addressing Clarify Unassigned Edge Case). 
    Create topic subdirectories dynamically based entirely on `doc.folder_path` -- create the directory if it doesn't exist, and drop any dependency on `FOLDER_ROUTING` (addressing Unnecessary Dependency on FOLDER_ROUTING).
    Use `extract_pdf_segment` from `src.processing.split` to write the files.
    Return a `per_page` list mapping `page_index` to `output_file` (relative path). Update tests in `test_organizer.py`.
  </action>
  <acceptance_criteria>
    - FileOrganizer computes min/max year per tenant correctly across all documents.
    - Unassigned pages (e.g. "Unassigned (2020-05)") are grouped under "Unassigned" for date aggregation.
    - Tenant directories include timeline, and Unassigned fallback to `غير محدد/` when no dates exist.
    - Subdirectories are created dynamically using `doc.folder_path` without importing `FOLDER_ROUTING`.
    - `organize()` method returns a list of dictionaries mapping `page_index` to relative `output_file`.
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/test_organizer.py -k "test_create_house_directory or test_tenant_directories_timeline or test_on_demand_topic_creation or test_unassigned_folder_period" -x</automated>
  </verify>
</task>

<task type="auto">
  <name>Task 2: Implement Reconciliation Logic</name>
  <files>src/processing/organizer.py, tests/test_organizer.py</files>
  <read_first>
    - src/processing/organizer.py
  </read_first>
  <action>
    Implement a module-level `run_reconciliation(summary: dict, per_page: list, total_input_pages: int, house_id: str, output_dir: Path)` function. 
    It writes the reconciliation manifest to `output_dir / f"{house_id}_manifest.json"` following the D-07 structure atomically (using temp file and replace). 
    If `total_input_pages != summary['total_output_pages']`, raise a `RuntimeError("Reconciliation failed: total input pages != total output pages")`. Update tests in `test_organizer.py`.
  </action>
  <acceptance_criteria>
    - `run_reconciliation` creates a temporary JSON file and replaces the target manifest atomically.
    - It raises `RuntimeError` precisely when `total_input_pages` does not match `summary['total_output_pages']`.
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/test_organizer.py -k "test_page_count_reconciliation or test_reconciliation_manifest" -x</automated>
  </verify>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| FileSystem | Output paths must not traverse outside the designated output directory |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-04-01 | Tampering | organizer.py | high | mitigate | Use utils.sanitize_filename and bound output_base_dir to prevent directory traversal |
| T-04-02 | Denial of Service | split.py | low | accept | Decompression bomb mitigation already present in split.py |
</threat_model>

<verification>
FileOrganizer correctly routes files to safe, properly formatted Arabic directory structures and reconciliation safely identifies any page leaks.
</verification>

<success_criteria>
`pytest tests/test_organizer.py` passes completely.
</success_criteria>

<output>
Create `.planning/phases/04-output-structure-reconciliation/04-01-SUMMARY.md` when done
</output>
