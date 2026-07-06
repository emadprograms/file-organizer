---
phase: 09
slug: final-e2e-sweep-fix-absolute-pdf-indexing-array-bounds-align
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-05
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x+ |
| **Config file** | none |
| **Quick run command** | `pytest tests/test_indexing.py tests/test_routing.py` |
| **Full suite command** | `pytest tests/test_indexing.py tests/test_llm.py tests/test_pipeline.py tests/test_routing.py` |
| **Estimated runtime** | ~105 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_indexing.py tests/test_routing.py`
- **After every plan wave:** Run `pytest tests/test_indexing.py tests/test_llm.py tests/test_pipeline.py tests/test_routing.py`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01 | 01 | 1 | CLN-08 | — | Validates indices before fitz slicing | unit | `pytest tests/test_indexing.py` | ✅ | ✅ green |
| 09-02 | 01 | 1 | LOG-02 | — | Writes trace JSONs; logs token usage | unit | `pytest tests/test_llm.py` | ✅ | ✅ green |
| 09-03 | 01 | 1 | GRP-06 | — | No None dates before Pass 2 | unit | `pytest tests/test_pipeline.py` | ✅ | ✅ green |
| 09-04 | 01 | 1 | OUT-06 | — | Fatal error on page loss; safe fallback | e2e | `pytest tests/test_pipeline.py` | ✅ | ✅ green |
| 09-05 | 01 | 1 | OUT-06 | — | Routes index errors to "Unassigned" | unit | `pytest tests/test_routing.py` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_indexing.py` — tests for boundary validation
- [x] `tests/test_llm.py` — tests for trace file creation
- [x] `tests/test_pipeline.py` — tests for date resolution and page reconciliation
- [x] `tests/test_routing.py` — tests for fallback routing

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Trace File Contents | LOG-02 | Verify JSON schema | Check `logs/traces/` for expected keys |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-06
