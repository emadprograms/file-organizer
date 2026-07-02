---
phase: 6
slug: refactor-the-src-folder-into-a-clear-folder-structure
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-03T00:25:00Z
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none |
| **Quick run command** | pytest tests/ |
| **Full suite command** | pytest tests/ |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run pytest tests/
- **After every plan wave:** Run pytest tests/
- **Before /gsd-verify-work:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 6-01-01 | 01 | 1 | N/A | — | N/A | unit | pytest tests/ | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have <automated> verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] 
yquist_compliant: true set in frontmatter

**Approval:** approved 2026-07-03
