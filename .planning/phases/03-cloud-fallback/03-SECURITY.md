---
phase: "03"
name: "cloud-fallback"
threats_open: 0
---

# Security Audit: Phase 03

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation / Evidence | Status |
|-----------|----------|-----------|-------------|-----------------------|--------|
| T-03-01 | Information Disclosure | Configuration | Mitigate | API keys are read via `os.getenv()` rather than hardcoded. Confirmed in `src/llm.py` `GemmaClient.__init__`. | CLOSED |
| T-03-02 | Denial of Service | External APIs | Mitigate | Max 3 retries per provider prevents infinite loops. Confirmed in `src/llm.py` `_route_llm_call`. | CLOSED |
| T-03-03 | Denial of Service | External APIs | Mitigate | API calls are wrapped in `ThreadPoolExecutor` with a `timeout=90`. Confirmed in `src/llm.py` `_route_llm_call`. | CLOSED |
| T-03-04 | Tampering | External APIs | Mitigate | Communication uses secure `https://` base URLs. Confirmed in `src/llm.py` `GemmaClient.__init__`. | CLOSED |

## Accepted Risks
- **Logging**: Detailed responses are not logged to prevent PII exposure, which slightly reduces repudiation capabilities but is an accepted privacy tradeoff.

## Security Audit 2026-06-27
| Metric | Count |
|--------|-------|
| Threats found | 4 |
| Closed | 4 |
| Open | 0 |
