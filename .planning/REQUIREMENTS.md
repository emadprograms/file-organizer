# Requirements for v1.1

## Clean Up & Refactor
- [ ] **REF-01**: Delete all redundant code and unused logic.
- [ ] **REF-02**: Remove local model support completely.
- [ ] **REF-03**: Simplify the API key usage and switching process.

## Cloud-Only Migration
- [ ] **CLOUD-01**: Implement primary LLM requests using Gemini.
- [ ] **CLOUD-02**: Implement fallback to OpenRouter when Gemini fails.
- [ ] **CLOUD-03**: Implement fallback to Groq when OpenRouter fails.

## Hardening
- [ ] **TEST-01**: Add comprehensive unit and integration tests.
- [ ] **TEST-02**: Audit and fix existing bugs.

## Out of Scope
- Local model execution.
