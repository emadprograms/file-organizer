---
phase: 04-output-structure-reconciliation
plan: 02
type: execute
wave: 2
depends_on: [04-01-file-organizer]
files_modified:
  - src/organize.py
  - tests/test_pipeline_pass2.py
autonomous: true
requirements: [DIFF-02, OUT-06]
must_haves:
  truths:
    - Pass 2 skips LLM grouping if the grouped.json checkpoint exists
    - Pipeline fails with RuntimeError if reconciliation fails
    - Both checkpoints are deleted after a successful reconciliation
  artifacts:
    - src/organize.py
  key_links:
    - FileOrganizer integration in organize.py

## Artifacts this phase produces
- `output/checkpoints/grouped.json` (checkpoint file, new path pattern)
---

<objective>
Integrate the Pass 2 checkpoint and the new FileOrganizer + run_reconciliation logic into the main pipeline.

Purpose: Enable resume-ability for Pass 2 and enforce the final reconciliation checks end-to-end.
Output: Updated organize.py wiring.
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
  <name>Task 1: Pass 2 Checkpoint & Resume</name>
  <files>src/organize.py, tests/test_pipeline_pass2.py</files>
  <read_first>
    - src/organize.py
    - src/core/schemas.py
  </read_first>
  <action>
    In `main()`, implement checkpointing for Pass 2 (DIFF-02, D-05). 
    Check for checkpoint path constructed strictly using `args.target_dir / "output" / "checkpoints" / "grouped.json"` (addressing Align Paths). 
    If it exists, load documents from it (`[DocumentGroup(**d) for d in json.load(f)]`). 
    If not, run `pipeline._group_and_route_documents()` and save the result as JSON (`[doc.model_dump() for doc in documents]`). 
    Ensure the checkpoint is written atomically (temp file and replace). Update tests.
  </action>
  <acceptance_criteria>
    - `args.target_dir / "output" / "checkpoints" / "grouped.json"` is correctly used for checking, reading, and writing.
    - Application resumes from `grouped.json` skipping LLM calls if it exists.
    - Checkpoint file is written atomically.
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/test_pipeline_pass2.py -x</automated>
  </verify>
</task>

<task type="auto">
  <name>Task 2: Wire Organizer and Reconciliation</name>
  <files>src/organize.py, tests/test_pipeline_pass2.py</files>
  <read_first>
    - src/organize.py
    - src/processing/organizer.py
  </read_first>
  <action>
    Update `main()` to instantiate `FileOrganizer` using `args.target_dir / "output" / house_id` as the output directory. 
    Call `organize()` and capture the returned `per_page` mapping. 
    Import `fitz` and calculate `total_input_pages` directly using `fitz.open(pdf_path).page_count` (addressing Calculate Source Pages via PyMuPDF).
    Construct the `summary` dictionary (tracking output pages and file count). 
    Call `run_reconciliation` (OUT-06) with `total_input_pages` and `house_id`. 
    If it returns successfully, delete both checkpoints (`cleaned.json` and `grouped.json`) as per D-06. If it raises, checkpoints remain intact. Update tests.
  </action>
  <acceptance_criteria>
    - `total_input_pages` is computed via `fitz.open(pdf_path).page_count`.
    - `FileOrganizer` is instantiated with the properly resolved `output_dir`.
    - Checkpoint deletion only happens after `run_reconciliation` succeeds.
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/test_pipeline_pass2.py -x</automated>
  </verify>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Checkpoint Files | Local disk state dictates pipeline progression |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-04-03 | Tampering | organize.py | medium | mitigate | Checkpoints use atomic file writes to prevent partial JSON corruption. |
</threat_model>

<verification>
Pipeline efficiently skips Pass 2 when checkpoint exists and strictly enforces reconciliation before deleting checkpoints.
</verification>

<success_criteria>
`pytest` passes completely for all test suites.
</success_criteria>

<output>
Create `.planning/phases/04-output-structure-reconciliation/04-02-SUMMARY.md` when done
</output>
