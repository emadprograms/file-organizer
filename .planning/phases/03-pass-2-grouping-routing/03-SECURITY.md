---
threats_open: 0
---
# Security Audit - Phase 3

## Threat Model (Retroactive STRIDE)

| Threat ID | Category | Severity | Disposition | Mitigation Expected |
|-----------|----------|----------|-------------|---------------------|
| T-GRP-01 | Denial of Service | high | mitigate | Hard fail on continuous LLM errors via a loop counter |
| T-GRP-02 | Tampering | high | mitigate | Programmatic verification of LLM grouping output to prevent gaps and overlaps |
| T-ROUT-01 | Elevation of Privilege | high | mitigate | Restrict LLM routed folder to explicitly allowed folders for that category |
| T-ROUT-02 | Denial of Service | medium | mitigate | Fallback to a safe default if LLM fails or returns invalid folders |

## Accepted Risks Log
None.

## Threat Verification

| Threat ID | Category | Severity | Disposition | Status | Evidence |
|-----------|----------|----------|-------------|--------|----------|
| T-GRP-01 | Denial of Service | high | mitigate | CLOSED | src/processing/grouping.py:130 (`total_failures >= MAX_TOTAL_FAILURES`) |
| T-GRP-02 | Tampering | high | mitigate | CLOSED | src/processing/grouping.py:60 (`verify_groups`) |
| T-ROUT-01 | Elevation of Privilege | high | mitigate | CLOSED | src/processing/routing.py:101 (`if selected in allowed_folders:`) |
| T-ROUT-02 | Denial of Service | medium | mitigate | CLOSED | src/processing/routing.py:110 (`return "13_others", False`) |

## Security Audit 2026-07-04
| Metric | Count |
|--------|-------|
| Threats found | 4 |
| Closed | 4 |
| Open | 0 |

## Security Audit 2026-07-04 (Update)
| Metric | Count |
|--------|-------|
| Threats found | 4 |
| Closed | 4 |
| Open | 0 |
