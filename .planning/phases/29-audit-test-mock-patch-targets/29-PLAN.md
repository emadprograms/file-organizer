---
wave: 1
depends_on: []
files_modified:
  - tests/test_root_main_cli.py
autonomous: true
---

# Phase 29: Audit Test Mock Patch Targets Plan

## Goal
Ensure all test files patch mock targets at the import site instead of the definition site to prevent accidental coverage gaps or runtime errors.

## Requirements Covered
- **ARCH-05**: Audit Test Mock Patch Targets

<threat_model>
ASVS Level: 1
Blocking Threshold: High
Threats: Silent failure of mocked targets.
Mitigations: Code inspection and full test validation.
</threat_model>

## Tasks
1. Audit `@patch` across all tests for invalid import site targeting.
2. Update `test_root_main_cli.py` to correctly mock runner passes at `src.main`.
3. Verify test suite.
