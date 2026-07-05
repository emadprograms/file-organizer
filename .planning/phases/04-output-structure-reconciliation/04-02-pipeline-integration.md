---
phase: 04-output-structure-reconciliation
plan: 02
type: execute
wave: 2
depends_on: [01]
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
  <action>In `main()`, implement checkpointing for Pass 2 (DIFF-02, D-05). Check for `output/checkpoints/grouped.json`. If it exists, load documents from it (`DocumentGroup(**d)`). If not, run `pipeline._group_and_route_documents()` and save the result as JSON (`doc.model_dump()`). Ensure the checkpoint is written atomically. Update tests.</action>
  <verify>
    <automated>pytest tests/test_pipeline_pass2.py -x</automated>
  </verify>
  <done>Pipeline can resume from grouped.json without re-running Pass 2 LLM grouping.</done>
</task>

<task type="auto">
  <name>Task 2: Wire Organizer and Reconciliation</name>
  <files>src/organize.py, tests/test_pipeline_pass2.py</files>
  <action>Update `main()` to instantiate `FileOrganizer` using the `house_id`. Call `organize()` and capture the returned `per_page` mapping. Construct the `summary` dictionary (tracking output pages and file count). Call `run_reconciliation` (OUT-06). If it returns successfully, delete both checkpoints (`cleaned.json` and `grouped.json`) as per D-06. If it raises, checkpoints remain intact. Update tests.</action>
  <verify>
    <automated>pytest tests/test_pipeline_pass2.py -x</automated>
  </verify>
  <done>Pipeline seamlessly runs FileOrganizer, generates manifest, and cleans up checkpoints on success.</done>
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
