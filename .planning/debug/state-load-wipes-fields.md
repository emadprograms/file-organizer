---
status: resolved
trigger: |
  DATA_START
  Fix finding 1: state.load() wipes in-memory data after folder rename in run_generation_pass.
  In src/pipeline/runner.py, after run_reconciliation writes a new State instance, state.load()
  is called which overwrites populated in-memory cleaned_pages, grouped_documents,
  fine_categorized_pages with nulls from the new disk file (which only has the manifest at that point).
  Fix this so the reload picks up the manifest without wiping other already-populated fields.
  DATA_END
---
# Debug Session: state.load() wipes fields after folder rename

## Symptoms
- **Expected behavior**: After run_reconciliation, state.load() should pick up the manifest written to disk without overwriting already-populated in-memory fields (cleaned_pages, grouped_documents, fine_categorized_pages).
- **Actual behavior**: state.load() calls self.data.update(content) which overwrites all fields with whatever is on disk. Since the reconciliation State instance only wrote manifest+routed_documents, the calling state object loses cleaned_pages/grouped_documents/fine_categorized_pages.
- **Error messages**: None — silent data loss.
- **Key files**: src/pipeline/runner.py L282-285, src/core/state.py L24-40

## Current Focus
- hypothesis: State.load() uses self.data.update(content) which replaces ALL keys. The fix is to only update the manifest key from disk after reconciliation, not blindly reload everything.
- next_action: Fixed.

## Resolution
- **root_cause**: In `src/pipeline/runner.py`, `state.load()` reloaded the entire state file from disk, overwriting in-memory `cleaned_pages`, `grouped_documents`, and `fine_categorized_pages` with `None` values because the state file on disk only had the manifest produced by reconciliation.
- **fix**: Replaced `state.load()` with targeted extraction of `manifest` from disk if present, preserving all in-memory arrays.
- **files_changed**: src/pipeline/runner.py

