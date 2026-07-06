---
phase: 07
slug: cross-phase-integration-fixes-tenant-date-mapping-relative-i
status: validated 2026-07-06
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-05
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | none |
| **Quick run command** | `pytest` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency**: 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | GRP-01 | — | N/A | unit | `pytest tests/test_pipeline_pass2.py` | ✅ | ✅ green |
| 07-01-02 | 01 | 1 | OUT-02 | — | N/A | unit | `pytest tests/test_organizer.py` | ✅ | ✅ green |
| 07-01-03 | 01 | 1 | LOG-04 | — | N/A | unit | `pytest tests/test_organizer.py` | ✅ | ✅ green |
| 07-01-04 | 01 | 1 | LLM-08 | — | N/A | unit | `pytest tests/test_phase7_features.py` | ✅ | ✅ green |
| 07-01-05 | 01 | 1 | GRP-10 | — | N/A | unit | `pytest tests/test_phase7_features.py` | ✅ | ✅ green |

---

## Wave 0 Requirements

- [x] `tests/test_pipeline_pass2.py` — stubs for GRP-01
- [x] `tests/test_organizer.py` — stubs for OUT-02, LOG-04
- [x] `tests/test_phase7_features.py` — stubs for LLM-08, GRP-10

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dry-Run Visuals | OUT-02 | Visual layout of `rich.tree.Tree` | Run `python src/organize.py ./pdfs/1273 --dry-run` and verify the tree structure |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-06

