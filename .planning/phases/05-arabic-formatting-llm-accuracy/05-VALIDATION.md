---
phase: 05
slug: arabic-formatting-llm-accuracy
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-23
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none |
| **Quick run command** | `pytest tests/test_phase_05.py` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_phase_05.py`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | ARABIC-01 | — | N/A | unit | `pytest tests/test_phase_05.py::test_arabic_string_safety` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | ARABIC-02 | — | N/A | unit | `pytest tests/test_phase_05.py::test_zero_padded_folders` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | ARABIC-03 | — | N/A | unit | `pytest tests/test_phase_05.py::test_dynamic_folder_generation` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | LLM-01 | — | N/A | unit | `pytest tests/test_phase_05.py::test_identity_preservation_prompt` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 2 | LLM-02 | — | N/A | unit | `pytest tests/test_phase_05.py::test_reliable_retries_and_fallback` | ❌ W0 | ⬜ pending |
| 05-02-03 | 02 | 2 | LLM-03 | — | N/A | unit | `pytest tests/test_phase_05.py::test_other_letters_catch_all` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase_05.py` — stubs for all Phase 5 requirements

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Verify actual Windows Explorer sorting | ARABIC-02 | OS-level UI behavior | Open output directory in Windows Explorer and ensure folders sort chronologically by prefix. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
