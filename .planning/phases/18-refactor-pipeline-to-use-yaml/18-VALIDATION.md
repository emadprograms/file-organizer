---
phase: 18
slug: refactor-pipeline-to-use-yaml
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-15
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 |
| **Config file** | none |
| **Quick run command** | `pytest tests/test_yaml_pipeline.py -x` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_yaml_pipeline.py -x`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | REQ-YAML-01 | — | N/A | unit | `pytest tests/test_yaml_pipeline.py::test_anchor_logic_bypass` | ✅ W0 | ✅ green |
| 18-01-02 | 01 | 1 | REQ-YAML-02 | — | N/A | unit | `pytest tests/test_yaml_pipeline.py::test_timeline_fallback_overlap` | ✅ W0 | ✅ green |
| 18-01-03 | 01 | 1 | REQ-YAML-03 | — | N/A | unit | `pytest tests/test_yaml_pipeline.py::test_timeline_fallback_no_date` | ✅ W0 | ✅ green |
| 18-02-01 | 02 | 2 | REQ-FILES-01 | — | N/A | integration | `pytest tests/test_file_placement.py` | ✅ W0 | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_yaml_pipeline.py` — stubs for YAML loading, anchor bypass, and timeline mapping
- [x] `tests/test_file_placement.py` — stubs for `.source_files` hiding and PDF placement checks
- [x] `tests/conftest.py` — shared fixtures for mock documents and YAML files

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Auto-generation of YAML | REQ-YAML-GEN | Real LLM required for extraction | Run pipeline without YAML and verify `tenants.yaml` is correctly generated. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
