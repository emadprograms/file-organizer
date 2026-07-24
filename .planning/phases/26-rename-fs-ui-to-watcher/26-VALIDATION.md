---
phase: 26
slug: rename-fs-ui-to-watcher
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-24
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — tests discovered by convention |
| **Quick run command** | `pytest tests/test_e2e_watcher.py tests/test_watcher_append_mock.py tests/test_watcher_lock.py tests/test_watcher_orchestrator.py -v` |
| **Full suite command** | `python -m pytest tests/ -q --tb=short` |
| **Estimated runtime** | ~1 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick tests
- **After every plan wave:** Run `python -m pytest tests/ -q --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 26-01-01 | 01 | 1 | ARCH-02 | — | N/A | unit | `pytest tests/test_watcher_lock.py -v` | ✅ | ✅ green |
| 26-01-02 | 02 | 1 | ARCH-02 | — | N/A | unit | `pytest tests/test_watcher_orchestrator.py -v` | ✅ | ✅ green |
| 26-01-03 | 03 | 1 | ARCH-02 | — | N/A | e2e | `pytest tests/test_e2e_watcher.py -v` | ✅ | ✅ green |
| 26-01-04 | 04 | 1 | ARCH-02 | — | N/A | e2e | `pytest tests/test_watcher_append_mock.py -v` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. The refactoring involves renaming, so existing test logic under `tests/test_watcher_*.py` automatically validates functionality.*
