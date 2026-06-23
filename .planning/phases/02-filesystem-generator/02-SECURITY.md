---
phase: 2
slug: filesystem-generator-gui
status: SECURED
threats_open: 0
asvs_level: 1
created: 2026-06-23
---

# Phase 2 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Application -> Filesystem | Writing to local directories | PDF bytes, directory names |
| User -> GUI | Inputting paths | File paths |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| TR-2-01 | Tampering | Path generation | mitigate | `_sanitize_filename` removes illegal chars | closed |
| TR-2-02 | DoS | Path length | mitigate | `_sanitize_filename` truncates names to 50 chars | closed |
| TR-2-03 | Spoofing | GUI path input | accept | Local desktop app, user trusts local files | closed |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-2-01 | TR-2-03 | GUI allows any path. Local desktop app assumption accepts this risk. | Project Owner | 2026-06-23 |

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
- [x] `status: SECURED` set in frontmatter

**Approval:** verified 2026-06-23
