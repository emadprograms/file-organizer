---
phase: 03
slug: api-key-cycling-telemetry
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-23
---

# Phase 03 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Application / Google API | Outbound API requests to Gemini | API keys, text data |
| Main Thread / Worker | Internal state sharing | Telemetry statistics |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-03-01 | Exposure of Sensitive Information | telemetry.log / GUI dashboard | mitigate | `src/llm.py` uses `key_index` instead of raw keys; `src/gui.py` uses `Key_{i}` format | closed |
| T-03-02 | Concurrency Race Conditions & UI Freezes | Internal state / GUI | mitigate | `src/llm.py` sleeps outside lock; `src/gui.py` uses lock-free `queue.Queue` | closed |
| T-03-03 | Rate Limit Cascade | rate limiter / retries | mitigate | API calls routed through `_get_client_and_key()`; Global RPM cap of 15 | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-23 | 3 | 3 | 0 | gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-23
