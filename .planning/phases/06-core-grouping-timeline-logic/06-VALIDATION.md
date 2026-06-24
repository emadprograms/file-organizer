---
phase: 6
slug: core-grouping-timeline-logic
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-24
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest tests/test_timeline_logic.py` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_timeline_logic.py`
- **After every plan wave:** Run `pytest tests/`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | REQ-LOGIC-01 | — | N/A | unit | `pytest tests/test_timeline_logic.py::test_logic_01_large_family` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | REQ-LOGIC-02 | — | N/A | unit | `pytest tests/test_timeline_logic.py::test_logic_02_array_order` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | REQ-LOGIC-03 | — | N/A | unit | `pytest tests/test_timeline_logic.py::test_logic_03_single_word_names` | ❌ W0 | ⬜ pending |
| 06-01-04 | 01 | 1 | REQ-LOGIC-04 | — | N/A | unit | `pytest tests/test_timeline_logic.py::test_logic_04_date_grouping` | ❌ W0 | ⬜ pending |
| 06-01-05 | 01 | 1 | REQ-LOGIC-05 | — | N/A | unit | `pytest tests/test_timeline_logic.py::test_logic_05_prefix_rescue` | ❌ W0 | ⬜ pending |
| 06-01-06 | 01 | 1 | REQ-LOGIC-06 | — | N/A | unit | `pytest tests/test_timeline_logic.py::test_logic_06_non_anchor_routing` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_timeline_logic.py` — stubs for all 6 logic requirements

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
