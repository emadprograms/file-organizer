# Security Report

## Threat Register (Retroactive)
| Threat ID | Category | Disposition | Mitigation Plan |
|-----------|----------|-------------|-----------------|
| TR-01 | Denial of Service | mitigate | Use tenacity exponential backoff and staggered sleeps for LLM API rate limits |
| TR-02 | Tampering | mitigate | Validate LLM JSON output using Pydantic schemas |
| TR-03 | Information Disclosure | mitigate | Load API keys from environment variables (.env) |
| TR-04 | Tampering | mitigate | Sanitize LLM-generated output filenames against path traversal |
| TR-05 | Tampering | mitigate | Use thread locks when writing to the concurrent JSON cache |
| TR-06 | Information Disclosure | accept | Sending PII (resident names/docs) to external Google Gemma API |

## Accepted Risks Log
(None)
