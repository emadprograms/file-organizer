---
phase: 33
slug: 33-bidirectional-reconciliation-engine
status: final
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-01
---

# Phase 33 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 |
| **Config file** | none |
| **Quick run command** | `pytest tests/test_reconcile_bidirectional.py` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~1 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_reconcile_bidirectional.py`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 33-01-01 | 01 | 1 | RECON-01,02,07 | — | N/A | e2e | `pytest tests/test_reconcile_bidirectional.py` | ✅ | ✅ green |
| 33-01-02 | 01 | 1 | RECON-03,04 | — | N/A | e2e | `pytest tests/test_reconcile_bidirectional.py` | ✅ | ✅ green |
| 33-01-03 | 01 | 1 | RECON-05 | — | N/A | e2e | `pytest tests/test_reconcile_bidirectional.py` | ✅ | ✅ green |
| 33-01-04 | 01 | 1 | RECON-06 | — | N/A | e2e | `pytest tests/test_reconcile_bidirectional.py` | ✅ | ✅ green |

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
