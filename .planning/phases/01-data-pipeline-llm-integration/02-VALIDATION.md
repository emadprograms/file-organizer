---
phase: 02
slug: llm-integration
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-21
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini or pyproject.toml |
| **Quick run command** | `python -m pytest tests/test_llm.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~30 seconds (mocked), ~120 seconds (live API) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_llm.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|--------------------|--------|
| 02-01-01 | 01 | 1 | LLM-01 | unit | `pytest tests/test_llm.py::test_api_connection` | ✅ green |
| 02-01-02 | 01 | 1 | LLM-01 | unit | `pytest tests/test_llm.py::test_schema_definition` | ✅ green |
| 02-02-01 | 02 | 1 | LLM-02, LLM-03 | integration | `pytest tests/test_llm.py::test_page_classification` | ✅ green |
| 02-02-02 | 02 | 1 | LLM-04 | integration | `pytest tests/test_llm.py::test_category_classification` | ✅ green |
| 02-03-01 | 03 | 2 | LLM-05 | integration | `pytest tests/test_llm.py::test_continuation_detection` | ✅ green |
| 02-03-02 | 03 | 2 | LLM-05 | integration | `pytest tests/test_llm.py::test_sliding_window` | ✅ green |

*Status: ⏳ pending → ✅ green → ❌ red → 🔄 flaky*

---

## Wave 0 Requirements

- [x] `tests/test_llm.py` — stubs for LLM-01 through LLM-05
- [x] `tests/conftest.py` — shared fixtures for mocked API responses
- [x] pytest installed — verify in requirements.txt

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Arabic name normalization accuracy | LLM-03 | Requires human judgement on name grouping | Run on 10 sample pages, verify name consistency |
| Category classification accuracy | LLM-04 | Requires domain knowledge to verify categories | Compare against 20-page golden set |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ✅ Approved

---

## Validation Audit 2026-06-21
| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
