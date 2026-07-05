---
phase: 06
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: 
  - src/processing/pipeline.py
  - src/processing/grouping.py
  - src/processing/organizer.py
  - src/processing/routing.py
  - src/organize.py
autonomous: true
requirements: [CLN-02, CLN-04, CLN-08, OUT-05, OUT-03, FS-04, LOG-04, GRP-04, GRP-12, LLM-08]
must_haves:
  truths: 
    - The pipeline creates all 13 subdirectories for every tenant automatically
    - Unassigned documents are placed in an appropriately named Arabic folder
    - Reconciliation reports print a detailed table before asserting correctness
    - Consecutive LLM routing failures fallback to '13_others' after 5 consecutive errors
  artifacts: 
    - Updated output directories matching specifications
    - Safe checkpoint files via atomic writes
  key_links: []
---

<objective>
Execute Phase 6 gap closures identified during the Milestone 1.0 Audit to ensure full pipeline correctness.

Purpose: Fix integration points between Pass 1, Pass 2, and the Output system to finalize the stable v1.0 milestone.
Output: Adjusted pipelines, resilient writes, and localized folder structures.
</objective>

<execution_context>
@.agents/gsd-core/workflows/execute-plan.md
@.agents/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/06-milestone-1-0-audit-gap-closures/06-RESEARCH.md
@.planning/phases/06-milestone-1-0-audit-gap-closures/06-CONTEXT.md
</context>

<tasks>

<task type="auto">
  <name>Task 06-01-01: Update configurations and schemas</name>
  <files>src/processing/pipeline.py, src/processing/grouping.py</files>
  <action>
    - In `src/processing/pipeline.py`, update `ANCHOR_CATEGORIES` to `{"contract", "forms", "id_cards"}` to match the JSON report categories (CLN-02, CLN-04, CLN-08).
    - In `src/processing/grouping.py`, append rule 5 to `GROUPING_PROMPT`: `5. You MUST provide a "reason" string for every group explaining why you grouped these pages together, based on what you saw and didn't see.` (GRP-04, GRP-12).
  </action>
  <verify>
    <automated>pytest tests/</automated>
  </verify>
  <done>ANCHOR_CATEGORIES perfectly matches JSON categories, and GROUPING_PROMPT explicitly requests the reason.</done>
</task>

<task type="auto">
  <name>Task 06-01-02: Fix Organizer logic and Output system</name>
  <files>src/processing/organizer.py</files>
  <action>
    - In `FileOrganizer.organize()`, immediately after generating `tenant_folder_names`, iterate over them and `FOLDER_ROUTING.keys()` to proactively create all 13 subdirectories (`os.makedirs(target_dir, exist_ok=True)`) (OUT-03).
    - Update Unassigned folder naming logic per D-01 to use `f"غير مخصص (فترة مستنتجة) {min_year}-{max_year}"` if dates exist, or `"غير مخصص"` if none (OUT-05).
    - Fix the direct-routed document logic per D-03 to apply a date-only filename (`YYYY-MM-DD.pdf`) to ALL direct-routed documents, fully honoring user decision D-03 over the conflicting RESEARCH.md finding (OUT-05).
    - In `run_reconciliation()`, use `rich.table.Table` to print a detailed breakdown (House ID, Total Input Pages, Total Output Pages, Output File Count, Unaccounted Pages) to the console per D-02 before running the `RuntimeError` check (LOG-04).
  </action>
  <verify>
    <automated>pytest tests/</automated>
  </verify>
  <done>All 13 subdirectories are explicitly created per tenant, the Unassigned folder is translated to Arabic, and reconciliation failures print the rich table first.</done>
</task>

<task type="auto">
  <name>Task 06-01-03: Implement state and atomicity</name>
  <files>src/processing/routing.py, src/organize.py, src/processing/organizer.py</files>
  <action>
    - In `src/processing/routing.py`, add a module-level `consecutive_routing_failures = 0`. In `route_document`, check if this is `>= 5`. If so, log a warning and return `("13_others", False)`. Increment on failure, reset on success (LLM-08).
    - In `src/organize.py` and `src/processing/organizer.py`, import `atomic_write` from `src.fs_utils`. Use the context manager `with atomic_write(filepath) as tmp_path:` for all JSON dumping, replacing manual `.tmp` file renaming for both checkpoint and manifest paths (FS-04).
  </action>
  <verify>
    <automated>pytest tests/</automated>
  </verify>
  <done>Consecutive LLM routing failures fallback gracefully and all JSON writes use the robust atomic rename utility.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Disk I/O | Output PDF generation and JSON manifest writes |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-06-01 | Tampering | Output files | medium | mitigate | Use atomic writes via `fs_utils.atomic_write` to ensure incomplete writes don't corrupt checkpoints |
| T-06-02 | Denial of Service | Routing LLM | medium | mitigate | Enforce 5-consecutive failure limit before skipping the LLM and defaulting to `13_others` |
</threat_model>

<verification>
pytest tests/
</verification>

<success_criteria>
- The 13 routing directories are pre-created.
- The `Unassigned` folder correctly shows the translated string.
- Detailed reconciliation table is printed to the console.
- Missing files and checkpoints no longer corrupt the system due to atomic writes.
- LLM failures over 5 bypass the LLM cleanly.
</success_criteria>

<output>
Create `.planning/phases/06-milestone-1-0-audit-gap-closures/06-01-SUMMARY.md` when done
</output>
