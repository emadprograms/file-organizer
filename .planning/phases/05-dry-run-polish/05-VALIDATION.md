---
phase: "05"
slug: dry-run-polish
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-05
audited: 2026-07-05
---

# Phase 05 — Validation Strategy

> Per-phase validation contract reconstructed from PLAN/SUMMARY artifacts (State B).
> Audit date: 2026-07-05 | Result: NYQUIST-COMPLIANT

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 |
| **Config file** | none (rootdir auto-detected: project root) |
| **Quick run command** | `python -m pytest tests/test_e2e.py tests/test_cli.py tests/test_pipeline.py tests/test_llm.py -v` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~14 seconds (phase tests only) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_e2e.py tests/test_cli.py tests/test_pipeline.py tests/test_llm.py -v`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Test Function | Test File | File Exists | Status |
|---------|------|------|-------------|-----------|---------------|-----------|-------------|--------|
| 05-01-01 | 1 | 1 | DIFF-01 | unit | `test_organize_dry_run_no_makedirs` | `tests/test_pipeline_pass2.py` | ✅ | ✅ green |
| 05-01-02 | 1 | 1 | DIFF-01 | unit | `test_dry_run_flag_in_parser` | `tests/test_cli.py` | ✅ | ✅ green |
| 05-01-03 | 1 | 1 | DIFF-01 | unit | `test_checkpoint_skip_on_dry_run` | `tests/test_pipeline_pass2.py` | ✅ | ✅ green |
| 05-01-04 | 1 | 1 | DIFF-01 | integration | `test_dry_run_end_to_end` | `tests/test_e2e.py` | ✅ | ✅ green |
| 05-02-01 | 2 | 2 | DIFF-01 | e2e | `test_dry_run_end_to_end` | `tests/test_e2e.py` | ✅ | ✅ green |
| 05-02-02 | 2 | 2 | DIFF-01 | unit | `test_validate_target_directory_missing_json` | `tests/test_cli.py` | ✅ | ✅ green |
| 05-02-03 | 2 | 2 | DIFF-01 | integration | `test_malformed_json_graceful_failure` | `tests/test_pipeline.py` | ✅ | ✅ green |
| 05-02-04 | 2 | 2 | DIFF-01 | unit | `test_llm_500_max_retries_halts` | `tests/test_llm.py` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

- `tests/test_e2e.py` — e2e dry-run coverage (created in Plan 2, Wave 2)
- `tests/test_cli.py` — CLI argument and validation coverage (pre-existing, extended)
- `tests/test_pipeline.py` — pipeline error handling (pre-existing, extended)
- `tests/test_llm.py` — LLM retry logic coverage (pre-existing, extended)
- `tests/test_pipeline_pass2.py` — unit tests for dry_run param in organizer (pre-existing, patched)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Arabic filenames render correctly on Windows terminal | DIFF-01 (D-01) | Terminal encoding (cp1252 vs utf-8) cannot be asserted reliably in subprocess CI | Run `python src/organize.py <house_dir> --dry-run` in a native Windows terminal; verify Arabic text in Tree/Table is legible without `?` replacement chars |
| Rich Tree/Table visual layout correctness | DIFF-01 (D-01) | Visual fidelity is subjective and cannot be pixel-tested via subprocess | Run a real dry-run and inspect the printed Tree/Table visually for House→Tenant→Category→PDF hierarchy |

---

## Validation Sign-Off

- [x] All tasks have automated verify commands
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0: existing infrastructure covered all phase requirements (no install needed)
- [x] No watch-mode flags used
- [x] Feedback latency ≤ 30s (actual: ~14s for phase tests)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-05

---

## Validation Audit 2026-07-05

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved (automated) | 8 tasks |
| Manual-only escalated | 2 behaviors |
| Test run result | 4/4 passed in 13.60s |
