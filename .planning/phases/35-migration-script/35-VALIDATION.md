---
phase: 35
slug: migration-script
status: passed
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-01T07:59:47Z
---

# Phase 35 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | none |
| **Quick run command** | `.venv/bin/python -m pytest tests/test_migration.py -v` |
| **Full suite command** | `.venv/bin/python -m pytest tests/test_migration.py -v` |
| **Estimated runtime** | ~1 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/python -m pytest tests/test_migration.py -v`
- **After every plan wave:** Run `.venv/bin/python -m pytest tests/test_migration.py -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 35-01-01 | 01 | 1 | MIGRATE-01 | — | N/A | unit | `.venv/bin/python -m pytest tests/test_migration.py` | ✅ | ✅ green |
| 35-01-02 | 01 | 1 | MIGRATE-02 | — | N/A | unit | `.venv/bin/python -m pytest tests/test_migration.py` | ✅ | ✅ green |
| 35-01-03 | 01 | 1 | MIGRATE-03 | — | N/A | unit | `.venv/bin/python -m pytest tests/test_migration.py` | ✅ | ✅ green |

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
