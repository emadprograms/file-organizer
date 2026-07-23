---
phase: 24
slug: fs-ui-orchestration
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-20
---

# Phase 24 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pytest.ini` / `.venv/bin/pytest` |
| **Quick run command** | `pytest tests/test_fs_ui_orchestrator.py tests/test_e2e_fs_ui.py` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_fs_ui_orchestrator.py`
- **After every plan wave:** Run `pytest tests/test_e2e_fs_ui.py`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 24-01-01 | 01 | 1 | N/A | — | FS UI Locking utility | unit | `pytest tests/test_fs_ui_lock.py` | ✅ | ✅ green |
| 24-02-01 | 02 | 1 | FSUI-04 | — | Process inbox and propose | integration | `pytest tests/test_fs_ui_orchestrator.py` | ✅ | ✅ green |
| 24-02-02 | 02 | 1 | FSUI-05 | — | Handle finalizations | integration | `pytest tests/test_fs_ui_orchestrator.py` | ✅ | ✅ green |
| 24-03-01 | 03 | 1 | FSUI-04, 05 | — | Full append mode propose and finalize | integration | `pytest tests/test_fs_ui_append_mock.py` | ✅ | ✅ green |
| 24-04-01 | 04 | 1 | FSUI-06 | — | Missing YAML abort | e2e | `pytest tests/test_e2e_fs_ui.py -k "missing_yaml"` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_fs_ui_lock.py` — unit tests for locking logic
- [x] `tests/test_fs_ui_orchestrator.py` — integration tests for orchestrator
- [x] `tests/test_fs_ui_append_mock.py` — integration tests for append mock
- [x] `tests/test_e2e_fs_ui.py` — e2e tests for fsui

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| E2E Append Mock UI Interaction | FSUI-04, 05 | Interactive UI | Manually drop a file into inbox and append " OK" to rename. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-24
