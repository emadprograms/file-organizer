---
phase: 1
slug: data-pipeline-llm-integration
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-22
---

# Phase 1 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Application -> Gemma API | External API calls to the LLM | Page images (potential PII) and classifications |
| Local Filesystem -> Application | Reading PDFs and writing output PDFs | PDF byte streams |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| TR-01 | DoS | Pipeline/LLM | mitigate | `src/llm.py` (@retry), `src/pipeline.py` (time.sleep) | closed |
| TR-02 | Tampering | LLM Client | mitigate | `src/llm.py` (PageClassification pydantic schemas) | closed |
| TR-03 | Information Disclosure | Configuration | mitigate | `src/main.py` (load_dotenv) | closed |
| TR-04 | Tampering | File output | mitigate | `src/main.py` (sanitize filenames) | closed |
| TR-05 | Tampering | Cache writing | mitigate | `src/pipeline.py` (threading.Lock for cache file writes) | closed |
| TR-06 | Information Disclosure | LLM Client | accept | Accepted risk for sending PII to external LLM API | closed |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-01 | TR-06 | Use of external Gemma API requires sending page images to Google's servers. | Project Owner | 2026-06-22 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-22 | 6 | 6 | 0 | gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-22
