---
phase: 22
slug: configuration-and-cli-modes
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-20
---

# Phase 22 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none |
| **Quick run command** | `pytest -v` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~1 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -v`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 22-01-01 | 01 | 1 | CONF-01 | — | N/A | unit | `pytest tests/test_core_config_parsing.py` | ✅ W0 | ✅ green |
| 22-02-01 | 02 | 2 | CONF-02 | — | N/A | unit | `pytest tests/test_root_main_cli.py` | ✅ W0 | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_core_config_parsing.py` — stubs for CONF-01
- [x] `tests/test_root_main_cli.py` — stubs for CONF-02

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved

## Post-Planning Gap Analysis
| Source | Item | Status |
|--------|------|--------|
| REQUIREMENTS.md | CONF-01 | ✓ Covered |
| REQUIREMENTS.md | CONF-02 | ✓ Covered |
| REQUIREMENTS.md | CONF-03 | ✓ Covered |
| CONTEXT.md | D-01 to D-08 | ✓ Covered |
