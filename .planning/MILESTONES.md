# Milestones History

## v5.2: Deep Architecture Integrity & Verification
**Shipped:** 2026-08-01

**Key Accomplishments:**
- Created robust `src/core/verification.py` module to deep-scan houses for file system integrity.
- Handled legacy artifacts, orphan vault files, missing shortcuts, and state vs. physical folder drift securely.
- Resolved tricky cross-platform edge cases involving Pytest mocked environments, `pylnk3`, and Windows long paths.
- Reached 100% passing test coverage (288 tests) across the entire system.

## v5.1: Polishing & Migration Cleanup
**Shipped:** 2026-08-01

**Key Accomplishments:**
- Unified `1_cleaned.json`, `2_grouped.json`, and `3_routed_and_finalized.json` into a single `state.json` file.
- Fixed the Timeline View document index numbering logic to properly jump indices relative to document page count.
- Expanded automated test coverage by refactoring tests away from legacy formats and creating `tests/test_live_e2e.py` targeting actual test sets.
- Fixed `pylnk3` Windows dependency resolution.
