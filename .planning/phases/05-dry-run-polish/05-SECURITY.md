---
phase: "05"
slug: dry-run-polish
status: verified
threats_open: 0
asvs_level: 1
created: 2026-07-05
mode: retroactive-STRIDE
---

# Phase 05 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> **Mode:** Retroactive-STRIDE — no `<threat_model>` block was present in PLAN files.
> The register was constructed from implementation files post-execution and verified at ASVS L1 depth.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| CLI → Filesystem | User-supplied `target_dir` path resolved and written to `output_base_dir` | Tenant names (Arabic PII), PDF content |
| CLI → LLM API | `LLMClient` sends page images/text to Gemini API | Housing document contents, tenant names |
| Subprocess → Process | E2E tests invoke CLI via `subprocess.run` | Test fixture paths, env vars (API key) |
| Checkpoint → Disk | `cleaned.json` / `grouped.json` written to `output/` subdirectory | Cleaned page data, grouped document metadata |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-05-S01 | Spoofing | `organize.py` — API key source | LOW | accept | Internal single-user CLI; no auth surface added by this phase | closed |
| T-05-T01 | Tampering | `organizer.py` — path traversal via `folder_path` | HIGH | mitigate | `target_dir.resolve()` + `str(target_dir).startswith(str(output_base_dir.resolve()))` check at L97-98; raises `ValueError` on violation | closed |
| T-05-T02 | Tampering | `organize.py` — checkpoint file bypass in dry-run | MEDIUM | mitigate | All write paths (`cleaned.json`, `grouped.json`, `manifest.json`) gated by `if not dry_run:`; read-only path confirmed L119-155 | closed |
| T-05-R01 | Repudiation | `organizer.py` — partial manifest write on crash | LOW | mitigate | Atomic write via `tmp_path.replace(manifest_path)` (L171-174); no partial manifest possible | closed |
| T-05-I01 | Info Disclosure | `organize.py` — API key in logs | LOW | mitigate | API key sourced from env only; only model name and paths logged; key never passed to logger | closed |
| T-05-I02 | Info Disclosure | `visualizer.py` — tenant names / filenames printed to terminal | LOW | accept | Internal operator tool; display of tenant data to operator is the intended function | closed |
| T-05-D01 | Denial of Service | `organize.py` / `llm.py` — LLM retry infinite loop | HIGH | mitigate | `test_llm_500_max_retries_halts` asserts `call_count <= 6`; `RuntimeError("LLM routing failed across all providers")` raised on exhaustion | closed |
| T-05-D02 | Denial of Service | `organize.py` — malformed `_report.json` crash | MEDIUM | mitigate | `test_malformed_json_graceful_failure` verifies non-zero exit and JSON error in stderr; no unhandled exception | closed |
| T-05-E01 | Elevation of Privilege | `organizer.py` — path traversal to arbitrary filesystem write | HIGH | mitigate | Same containment check as T-05-T01; `folder_path` from LLM output cannot escape `output_base_dir` | closed |

*Status: open · closed*
*Severity: critical > high > medium > low — only open threats at or above `high` count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-05-01 | T-05-S01 | Internal CLI tool with single operator; adding auth would be disproportionate. API key managed via `.env` / environment variable. | Emad (operator) | 2026-07-05 |
| AR-05-02 | T-05-I02 | Visualizer intentionally displays tenant names and filenames to the operator for dry-run preview. No external disclosure path exists. | Emad (operator) | 2026-07-05 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-07-05 | 9 | 9 | 0 | gsd-secure-phase (retroactive-STRIDE, ASVS L1) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-07-05
