---
phase: 04
slug: audit-fix
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-27
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest / mypy / ruff |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest tests/` |
| **Full suite command** | `pytest tests/ && mypy src/ && ruff check src/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/`
- **After every plan wave:** Run `pytest tests/ && mypy src/ && ruff check src/`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | REQ-04-01 | — | Fails fast instead of swallowing classification errors | unit | `pytest tests/test_pipeline.py` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | REQ-04-02 | — | Telemetry avoids unicode crash vulnerabilities by using standard logging | unit | `pytest tests/` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | REQ-04-03 | — | Types are statically verified | static | `mypy src/` | ✅ | ⬜ pending |
| 04-01-04 | 01 | 1 | REQ-04-04 | — | Mock API exhaustion is verified to throw an exception | unit | `pytest tests/test_llm.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_pipeline.py` — stubs for fail-fast verification
- [ ] `tests/test_llm.py` — stubs for API exhaustion mocks
- [ ] `pip install pytest mypy ruff` — ensure test framework and static analysis tools are installed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Output Consistency | REQ-04-E2E | Requires a realistic PDF document classification | Run the pipeline against a known sample PDF. Verify no exceptions, proper UTF-8 logging, and that final output groupings exactly match expectations. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-27
