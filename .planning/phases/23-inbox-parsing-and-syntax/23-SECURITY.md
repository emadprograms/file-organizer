---
phase: 23
slug: inbox-parsing-and-syntax
status: approved
threats_open: 0
created: 2026-07-20
---

# Phase 23 — Security Strategy

> Security threat model, mitigations, and verification for Phase 23.

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan | Verification Evidence | Status |
|-----------|----------|-----------|----------|-------------|-----------------|-----------------------|--------|
| T-23-01 | Spoofing | Parser | high | mitigate | Use strict whitespace splitting (`.split(maxsplit=5)`) and catch `ValueError` instead of crashing the listener loop. | `src/inbox/parser.py:11` | 🔒 CLOSED |
| T-23-02 | Information Disclosure | Resolver | medium | mitigate | Target directories are mapped exactly to predefined areas/groups, `resolve_area` scanning bounds strictly to `areas_root`. | `src/inbox/resolver.py:68` | 🔒 CLOSED |
| T-23-03 | Denial of Service | Resolver | high | mitigate | Restrict `group` values to strict enum ('1'-'13', 'G', 'U') to avoid unbounded matching/routing or LLM exhaustion. | `src/inbox/resolver.py:101` | 🔒 CLOSED |

*Status: 🔒 CLOSED · ⚠️ OPEN (blocking) · ℹ️ OPEN (non-blocking) · 📝 ACCEPTED RISK*

---

## Accepted Risks
*No accepted risks documented for this phase.*

---

## Audit Trail
### Security Audit 2026-07-20
| Metric | Count |
|--------|-------|
| Threats found | 3 |
| Closed | 3 |
| Open | 0 |
