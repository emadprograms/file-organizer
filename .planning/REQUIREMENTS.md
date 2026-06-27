# Requirements for v1.1

## Clean Up & Refactor

- [x] **REF-01**: Delete all redundant code and unused logic.
- [x] **REF-02**: Remove local model support completely.
- [x] **REF-03**: Simplify the API key usage and switching process.

## Cloud-Only Migration

- [x] **CLOUD-01**: Implement primary LLM requests using Gemini.
- [x] **CLOUD-02**: Implement fallback to OpenRouter when Gemini fails.
- [x] **CLOUD-03**: Implement fallback to Groq when OpenRouter fails.

## Hardening

- [ ] **TEST-01**: Add comprehensive unit and integration tests.
- [ ] **TEST-02**: Audit and fix existing bugs.

## Out of Scope

- Local model execution.
