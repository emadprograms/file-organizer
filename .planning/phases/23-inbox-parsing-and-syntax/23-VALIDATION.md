---
phase: 23
slug: inbox-parsing-and-syntax
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-20
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 |
| **Config file** | none |
| **Quick run command** | `python -m pytest tests/test_parser.py tests/test_resolver.py tests/test_root_main_append_mode.py` |
| **Full suite command** | `python -m pytest tests/` |
| **Estimated runtime** | ~55 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_parser.py tests/test_resolver.py tests/test_root_main_append_mode.py`
- **After every plan wave:** Run `python -m pytest tests/`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 55 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 23-01-01 | 01 | 1 | FSUI-01 | — | N/A | unit | `pytest tests/test_parser.py` | ✅ | ✅ green |
| 23-01-02 | 01 | 1 | FSUI-01 | — | N/A | unit | `pytest tests/test_parser.py` | ✅ | ✅ green |
| 23-01-03 | 01 | 1 | FSUI-01 | — | N/A | unit | `pytest tests/test_parser.py` | ✅ | ✅ green |
| 23-02-01 | 02 | 2 | FSUI-02 | — | N/A | unit | `pytest tests/test_resolver.py` | ✅ | ✅ green |
| 23-02-02 | 02 | 2 | FSUI-02 | — | N/A | unit | `pytest tests/test_resolver.py` | ✅ | ✅ green |
| 23-02-03 | 02 | 2 | FSUI-03 | — | N/A | unit | `pytest tests/test_resolver.py` | ✅ | ✅ green |
| 23-02-04 | 02 | 2 | FSUI-03 | — | N/A | unit | `pytest tests/test_root_main_append_mode.py` | ✅ | ✅ green |
| 23-02-05 | 02 | 2 | FSUI-03 | — | N/A | unit | `pytest tests/test_resolver.py` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-20
