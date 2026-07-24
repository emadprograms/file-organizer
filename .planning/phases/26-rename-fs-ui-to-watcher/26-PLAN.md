---
wave: 1
depends_on: []
files_modified:
  - src/watcher/__init__.py
  - src/watcher/lock.py
  - src/watcher/orchestrator.py
  - tests/test_e2e_watcher.py
  - tests/test_watcher_append_mock.py
  - tests/test_watcher_lock.py
  - tests/test_watcher_orchestrator.py
  - src/main.py
  - tests/test_pipeline_e2e.py
  - tests/test_root_main_append_mode.py
autonomous: true
---

# Phase 26: Rename `fs_ui/` to `watcher/` Plan

## Goal
Accurately describe the package responsibilities (file watching, locking) by renaming `fs_ui` to `watcher`.

## Requirements Covered
- **ARCH-02**: Rename `fs_ui/` to `watcher/`

<threat_model>
ASVS Level: 1
Blocking Threshold: High
Threats: Broken `unittest.mock` patch targets silently failing or erroring at runtime.
Mitigations: Rigorous test execution (`pytest`) to ensure no patches or imports are broken.
</threat_model>

## Tasks
1. Execute `git mv` for `src/fs_ui` and its tests.
2. Update all import sites and patch targets.
3. Verify test suite.
