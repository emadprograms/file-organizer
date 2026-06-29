---
phase: 01
slug: explore-alternatives-to-llm-classification
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-29
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | python script execution / manual comparison |
| **Config file** | none |
| **Quick run command** | `python scratch/classify_qwen_local.py` |
| **Full suite command** | `python scratch/classify_qwen_local.py` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python scratch/classify_qwen_local.py`
- **After every plan wave:** Run `python scratch/classify_qwen_local.py`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | REQ-1 | — | N/A | manual | `python scratch/classify_qwen_local.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scratch/classify_qwen_local.py` — skeleton for Qwen3-VL 4B implementation
- [ ] `ollama run qwen3-vl:4b` — local model setup

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual comparison | D-04 | Comparing predictions vs ground truth | Run local script and manually check JSON accuracy vs ground truth. |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
