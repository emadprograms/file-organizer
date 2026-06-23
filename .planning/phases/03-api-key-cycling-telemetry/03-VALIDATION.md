---
phase: 03
slug: api-key-cycling-telemetry
status: gaps_identified
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-23
gaps_identified: 2026-06-23
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest tests/ -m "not slow"` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -m "not slow"`
- **After every plan wave:** Run `pytest tests/`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | REQ-HARD-01 | — | N/A | unit | `pytest tests/test_llm.py` | ✅ W0 | ✅ green |
| 03-01-02 | 02 | 1 | REQ-HARD-01 | — | N/A | unit | `pytest tests/test_llm.py` | ✅ W0 | ✅ green |
| 03-01-03 | 03 | 1 | REQ-HARD-01 | — | N/A | unit | `pytest tests/test_llm.py` | ✅ W0 | ✅ green |
| 03-02-01 | 04 | 2 | REQ-HARD-03 | Exposure | Masked keys only | unit | `pytest tests/test_llm.py` | ✅ W0 | ✅ green |
| 03-03-01 | 05 | 3 | REQ-HARD-03 | — | N/A | manual | N/A | ✅ W0 | ✅ green |
| 03-03-02 | 06 | 3 | REQ-HARD-03 | Concurrency | Lock-free UI | manual | N/A | ✅ W0 | ✅ green |
| 03-04-01 | GAP | 4 | REQ-HARD-01 | Cascade | Global RPM cap | unit | `pytest tests/test_llm.py -k "global_rpm"` | ✅ W0 | ⬜ pending |
| 03-04-02 | GAP | 4 | REQ-HARD-01 | Cascade | Retry routing | unit | `pytest tests/test_llm.py -k "retry_route"` | ✅ W0 | ⬜ pending |
| 03-04-03 | GAP | 4 | REQ-HARD-01 | — | N/A | unit | `pytest tests/test_pipeline.py -k "sequential"` | ✅ W0 | ⬜ pending |
| 03-04-04 | GAP | 4 | REQ-HARD-01 | — | Graceful fallback | unit | `pytest tests/test_llm.py -k "invalid_response"` | ✅ W0 | ⬜ pending |
| 03-04-05 | GAP | 4 | REQ-HARD-01 | Cascade | Exponential backoff | unit | `pytest tests/test_llm.py -k "backoff"` | ✅ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_llm.py` — stubs for REQ-HARD-01
- [x] `tests/test_pipeline.py` — shared fixtures

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GUI Responsiveness | REQ-HARD-03 | Visual interaction | Observe Tkinter UI while large document processes |
| GUI Layout Update | REQ-HARD-03 | Visual verification | Verify that Tab 1 and Tab 2 are created successfully |
| Telemetry Dashboard | REQ-HARD-03 | Visual/Concurrency | Verify the Treeview updates live every ~500ms without stutter |
| Post-fix Throughput | REQ-HARD-01 | End-to-end | Run a 20+ page PDF and verify throughput is ~12-15 pages/min with zero 429 cascades |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved
