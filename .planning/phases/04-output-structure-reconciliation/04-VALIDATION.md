---
phase: 04
slug: output-structure-reconciliation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-05
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | none — see Wave 0 |
| **Quick run command** | `pytest tests/test_organizer.py -v` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_organizer.py -v`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | OUT-01 | — | N/A | unit | `pytest tests/test_organizer.py::test_create_house_directory -x` | ✅ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | OUT-02 | — | N/A | unit | `pytest tests/test_organizer.py::test_tenant_directories_timeline -x` | ✅ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | OUT-03 | — | N/A | unit | `pytest tests/test_organizer.py::test_on_demand_topic_creation -x` | ✅ W0 | ⬜ pending |
| 04-01-04 | 01 | 1 | OUT-04 | — | N/A | unit | `pytest tests/test_organizer.py::test_hardcoded_routing -x` | ✅ W0 | ⬜ pending |
| 04-01-05 | 01 | 1 | OUT-05 | — | N/A | unit | `pytest tests/test_organizer.py::test_unassigned_folder_period -x` | ✅ W0 | ⬜ pending |
| 04-01-06 | 01 | 1 | OUT-06 | — | N/A | unit | `pytest tests/test_organizer.py::test_page_count_reconciliation -x` | ✅ W0 | ⬜ pending |
| 04-01-07 | 01 | 1 | LOG-04 | — | N/A | unit | `pytest tests/test_organizer.py::test_reconciliation_manifest -x` | ✅ W0 | ⬜ pending |
| 04-01-08 | 01 | 1 | DIFF-02 | — | N/A | integration | `pytest tests/test_pipeline_pass2.py::test_checkpoint_resume -x` | ✅ W0 | ⬜ pending |
| 04-01-09 | 01 | 1 | DIFF-03 | — | N/A | unit | `pytest tests/test_organizer.py::test_reconciliation_manifest_generation -x` | ✅ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_organizer.py` — expand existing tests to cover Phase 4 rewrite logic.
- [ ] `tests/test_pipeline_pass2.py` — add test for checkpoint creation and loading.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | All | N/A | All phase behaviors have automated verification. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
