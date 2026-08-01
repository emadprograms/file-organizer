---
phase: 32
slug: pipeline-migration
status: final
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-01T07:58:13+03:00
---

# Phase 32 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 |
| **Config file** | none |
| **Quick run command** | `.venv/bin/pytest tests/test_main_file_placement.py` |
| **Full suite command** | `.venv/bin/pytest tests/` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest tests/test_main_file_placement.py`
- **After every plan wave:** Run `.venv/bin/pytest tests/`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 32-01-01 | 01 | 1 | TIMELINE-01 | — | N/A | integration | `.venv/bin/pytest tests/test_main_file_placement.py tests/test_e2e_watcher.py` | ✅ W0 | ✅ green |
| 32-01-02 | 01 | 1 | TIMELINE-02 | — | N/A | integration | `.venv/bin/pytest tests/test_main_file_placement.py tests/test_e2e_watcher.py` | ✅ W0 | ✅ green |
| 32-01-03 | 01 | 1 | TIMELINE-03 | — | N/A | integration | `.venv/bin/pytest tests/test_reconcile_core.py tests/test_e2e_watcher.py` | ✅ W0 | ✅ green |
| 32-01-04 | 01 | 1 | TIMELINE-04 | — | N/A | integration | `.venv/bin/pytest tests/test_main_file_placement.py tests/test_e2e_watcher.py` | ✅ W0 | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-08-01
