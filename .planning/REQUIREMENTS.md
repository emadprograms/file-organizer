# Requirements: File Categorizer Generalization

**Defined:** 2026-07-02
**Core Value:** Empower users to seamlessly categorize and organize any type of PDF by simply providing clear AI instructions and destination folders, without changing the underlying pipeline engine.

## v1 Requirements

### Code Hardening & Decoupling

- [ ] **REF-01**: Refactor `src/llm.py` to extract domain-specific prompts (Bahrain housing) and logic into external configuration, ensuring the core LLM client is fully generic.
- [ ] **REF-02**: Refactor `src/organizer.py` to remove hardcoded folder structures and entity parsing, driving organization entirely by YAML config rules and scripts.
- [ ] **REF-03**: Refactor `src/pipeline.py` to eliminate hardcoded heuristic strategies (e.g., timeline overrides, anchor categories), allowing these to be fully supplied via external Python scripts.
- [ ] **REF-04**: Port the extracted legacy logic into default fallback scripts or sample configurations to ensure the existing Bahrain housing use case remains 100% functional (backward compatibility).

## Out of Scope

| Feature | Reason |
|---------|--------|
| New extraction passes | Focus is on hardening the existing 4 passes and moving logic to config. |
| GUI / UI development | Tool remains CLI/config driven for now. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REF-01 | Phase 5 | Pending |
| REF-02 | Phase 5 | Pending |
| REF-03 | Phase 5 | Pending |
| REF-04 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 4 total
- Mapped to phases: 4
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-02*
*Last updated: 2026-07-02 after roadmap creation*
