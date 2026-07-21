---
status: resolved
phase: 24-fs-ui-orchestration
source: 24-01-SUMMARY.md, 24-02-SUMMARY.md
started: 2026-07-21T07:07:00Z
updated: 2026-07-21T18:23:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 2
name: Automated Coverage Confirmation
expected: |
  The following deliverables were automatically covered by passing unit tests:
  - D1: PID-based lock utility successfully acquires fresh locks, rejects conflicts from alive PIDs, and recovers stale locks from dead PIDs. (Covered by tests/test_fs_ui_lock.py)
  - D1: Orchestrator statelessly processes inbox and delays if size is unstable. (Covered by tests/test_fs_ui_orchestrator.py)
  - D2: Propose renames valid files to _Proposed.pdf and handles errors gracefully. (Covered by tests/test_fs_ui_orchestrator.py)
  - D3: Finalize invokes pipeline passes correctly after moving files safely to .source_files/. (Covered by tests/test_fs_ui_orchestrator.py)
  Confirm that no manual verification is needed for these items.
awaiting: user response

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server/service. Clear ephemeral state (temp DBs, caches, lock files). Start the application from scratch. Server boots without errors, any seed/migration completes, and a primary query (health check, homepage load, or basic API call) returns live data.
result: pass

### 2. Automated Coverage Confirmation
expected: The following deliverables were automatically covered by passing unit tests:
- D1: PID-based lock utility successfully acquires fresh locks, rejects conflicts from alive PIDs, and recovers stale locks from dead PIDs. (Covered by tests/test_fs_ui_lock.py)
- D1: Orchestrator statelessly processes inbox and delays if size is unstable. (Covered by tests/test_fs_ui_orchestrator.py)
- D2: Propose renames valid files to _Proposed.pdf and handles errors gracefully. (Covered by tests/test_fs_ui_orchestrator.py)
- D3: Finalize invokes pipeline passes correctly after moving files safely to .source_files/. (Covered by tests/test_fs_ui_orchestrator.py)
Confirm that no manual verification is needed for these items.
result: issue
reported: "Finalize / append mode is broken. It runs on the entire existing source files instead of the new file only, tenant timeline resolution with overlaps/hints is not implemented, and output destination/appending logic for _finalized.pdf is incorrect."

### 3. PID-based lock utility successfully acquires fresh locks, rejects conflicts from alive PIDs, and recovers stale locks from dead PIDs.
expected: PID-based lock utility successfully acquires fresh locks, rejects conflicts from alive PIDs, and recovers stale locks from dead PIDs.
result: pass
source: automated
coverage_id: D1

### 4. Orchestrator statelessly processes inbox and delays if size is unstable.
expected: Orchestrator statelessly processes inbox and delays if size is unstable.
result: pass
source: automated
coverage_id: D1

### 5. Propose renames valid files to _Proposed.pdf and handles errors gracefully.
expected: Propose renames valid files to _Proposed.pdf and handles errors gracefully.
result: pass
source: automated
coverage_id: D2

### 6. Finalize invokes pipeline passes correctly after moving files safely to .source_files/.
expected: Finalize invokes pipeline passes correctly after moving files safely to .source_files/.
result: pass
source: automated
coverage_id: D3

## Summary

total: 6
passed: 5
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Finalize invokes pipeline passes correctly after moving files safely to .source_files/"
  status: resolved
  reason: "User reported that finalize re-runs the entire pipeline on existing source files rather than only processing the new file, tenant assignment timeline logic is incorrect/not implemented for overlapping dates, and the destination structure is wrong."
  severity: blocker
  test: 2
  root_cause: "`FSUIOrchestrator.finalize` implements a manual, broken duplicate of the generation pass (merging JSONs, manual PDF appending, and partial tenant evaluation) instead of safely moving files to `.source_files/` and invoking the proper pipeline passes as originally intended."
  artifacts:
    - path: "src/fs_ui/orchestrator.py"
      issue: "`finalize()` manually reimplements pipeline logic with partial state instead of invoking the actual pipeline passes."
    - path: "src/main.py"
      issue: "The proper `run_generation_pass` (and reconciliation logic) is never invoked for the append lifecycle."
  missing:
    - "Refactor `finalize` to safely move the incoming `_Proposed OK.pdf` and its state to `.source_files/`"
    - "Invoke the standard pipeline passes that evaluate the entire global state to ensure correct tenant timeline resolution and destination structuring."
  debug_session: .planning/debug/finalize-pipeline-bug.md
