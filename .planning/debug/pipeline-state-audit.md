---
status: investigating
trigger: |
  DATA_START
  Investigate if there are other issues like the manifest=null bug — where the pipeline
  writes data to a separate State instance or separate path but the calling code's own
  State object is saved without reloading, causing data to be silently lost or
  incorrectly null in state.json. Also investigate whether there are other fields in
  state.json that are consistently null/empty when they shouldn't be, or whether the
  verification script has other silent false-passes similar to the manifest one.
  Do NOT make any changes. Diagnose only.
  DATA_END
---
# Debug Session: Similar issues to manifest-null bug

## Symptoms
- **Expected behavior**: All fields in state.json should be correctly populated after the pipeline runs. Verification should catch any missing data.
- **Actual behavior**: The manifest=null bug showed that run_reconciliation writes to its own State instance, so the calling code's state object misses the update. Other similar patterns may exist.
- **Error messages**: None visible — the concern is silent false-passes.
- **Timeline**: Discovered during investigation of Safra C/Safra Flats missing PDFs in UI.
- **Reproduction**: Audit the pipeline code (ingest, reconcile, runner, verification) for similar patterns.

## Current Focus
- hypothesis: There may be other places in the pipeline where a State instance is created internally by a called function, data is written and saved, but the calling scope's State object is never reloaded — causing fields to remain stale or null.
- next_action: gather initial evidence
