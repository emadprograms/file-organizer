---
phase: 01
slug: legacy-code-cleanup
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-07-07
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Local Filesystem | Boundary between the application and the user's filesystem | PDF files, JSON reports, log files |
| LLM API | Boundary between the local application and remote LLM providers | OCR text, Document structure, API keys |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-01 | Spoofing | LLM Client | high | mitigate | Pydantic schema validation for LLM responses (`src/processing/grouping.py`) | closed |
| T-01-02 | Tampering | File System | high | mitigate | Atomic writes (`os.replace`) used for checkpoints in `src/fs_utils.py` | closed |
| T-01-03 | Repudiation | Logger | medium | mitigate | `log_decision_trace` appends structured JSON audit logs in `src/logger.py` | closed |
| T-01-04 | Information Disclosure | LLM API | medium | accept | Document content sent to 3rd-party LLMs (Risk accepted for local usage) | closed |
| T-01-05 | Information Disclosure | Logger | low | accept | PII in debug logs on local filesystem without restrictive permissions | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-01-01 | T-01-04 | User provides API key explicitly, consenting to send their local document text to 3rd-party LLMs. | gsd-security-auditor | 2026-07-07 |
| R-01-02 | T-01-05 | Application runs locally on user's machine. User owns the data and logs, so strict OS-level file permissions are not enforced. | gsd-security-auditor | 2026-07-07 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-07-07 | 5 | 5 | 0 | gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-07-07
