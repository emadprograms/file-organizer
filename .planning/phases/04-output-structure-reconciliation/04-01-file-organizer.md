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
  <action>Rewrite `FileOrganizer` to accept `house_id` and use it to construct the output directory (per D-09, OUT-01). Implement tenant directory naming: `{canonical_arabic_name} {year_start}-{year_end}/` (D-02, OUT-02). Implement Unassigned directory naming: `غير محدد {year_start}-{year_end}/` (D-03, OUT-05). Create topic subdirectories on-demand only (D-04, OUT-03) using `FOLDER_ROUTING` (OUT-04). Use `extract_pdf_segment` from `src.processing.split` to write the files. Return a `per_page` list mapping `page_index` to `output_file` (relative path). Update tests in `test_organizer.py`.</action>
  <verify>
    <automated>pytest tests/test_organizer.py -k "test_create_house_directory or test_tenant_directories_timeline or test_on_demand_topic_creation or test_unassigned_folder_period" -x</automated>
  </verify>
  <done>FileOrganizer builds the correct directory structure, writes PDF segments, and returns the page mapping.</done>
</task>

<task type="auto">
  <name>Task 2: Implement Reconciliation Logic</name>
  <files>src/processing/organizer.py, tests/test_organizer.py</files>
  <action>Implement a module-level `run_reconciliation(summary: dict, per_page: list, total_input_pages: int, house_id: str, output_dir: Path)` function. It writes the reconciliation manifest to `output/{house_id}_manifest.json` following the D-07 structure (LOG-04, DIFF-03) atomically. If `total_input_pages != summary['total_output_pages']`, raise a `RuntimeError` (D-08, OUT-06). Update tests in `test_organizer.py`.</action>
  <verify>
    <automated>pytest tests/test_organizer.py -k "test_page_count_reconciliation or test_reconciliation_manifest" -x</automated>
  </verify>
  <done>run_reconciliation generates the manifest JSON and enforces page count equality via RuntimeError.</done>
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
