---
status: resolved
trigger: |
  DATA_START
  Fix finding 3: verification.py has 3 silent false-passes where checks trivially pass
  when data is null/empty because they guard add_error() behind non-zero conditions.
  1. Phase 48 (immutable page count): guarded by `if total_input_pages and ...` - passes with 0
  2. Phase 59 (report count vs vault docs): guarded by `if expected_report_count > 0` - passes with 0
  3. Timeline view check: guarded by `if not timeline_lnks and expected_count > 0` - passes with 0
  Fix all three so they fail explicitly when data is null/missing instead of passing trivially.
  DATA_END
---
# Debug Session: verification.py silent false-passes

## Symptoms
- **Expected behavior**: Verification should fail with a clear error when key data (manifest, report, timeline) is missing or empty.
- **Actual behavior**: Three checks in verification.py guard their error assertions behind non-zero conditions, so they trivially PASS when data is null/empty — giving false confidence.
- **Error messages**: None — false PASS results.
- **Key file**: src/core/verification.py

## Current Focus
- hypothesis: The three checks all have the same pattern: `if count > 0 and count != expected`. When count=0 (because data is null), the condition short-circuits and add_error is never called, so it falls through to add_pass.
- next_action: Fixed.

## Resolution
- **root_cause**: In `src/core/verification.py`, Phase 48 (page count), Phase 59 (report count), and Timeline View assertions were gated behind conditions like `if count > 0 and count != expected`, which allowed empty/null counts to skip error reporting and trivially pass.
- **fix**: 
  1. Phase 48: Flag explicit error if `total_input_pages` is 0 or missing in manifest summary.
  2. Phase 59: Flag explicit error if `expected_report_count` is 0 or does not match `len(report_data)`.
  3. Timeline View: Flag explicit error if `timeline_lnks` is empty or if `expected_timeline_count` is 0.
  4. Updated `test_verification_null_state_arrays` to assert failure (return code 1).
- **files_changed**: src/core/verification.py, tests/test_verification.py

