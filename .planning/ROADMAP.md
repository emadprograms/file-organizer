# Project Roadmap

## Milestone v1.1: Tech Debt & Cloud Migration

**5 phases** | **8 requirements mapped** | All covered ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Cleanup | Remove local model support and redundant code | REF-01, REF-02 | 2 |
| 2 | Key Mgmt | Simplify API key loading and switching | REF-03 | 2 |
| 3 | Cloud Fallback | Implement Gemini -> OpenRouter -> Groq chain | CLOUD-01, CLOUD-02, CLOUD-03 | 3 |
| 4 | Audit & Fix | Audit code for bugs and fix them | TEST-02 | 1 |
| 5 | Testing | Add tests and harden code | TEST-01 | 2 |

### Phase Details

### Phase 1: Cleanup
**Goal:** Remove local model support and redundant code
**Requirements:** REF-01, REF-02
**Success Criteria**:
1. Local model configuration and logic removed.
2. Unused legacy code paths deleted.

### Phase 2: Key Mgmt
**Goal:** Simplify API key loading and switching
**Requirements:** REF-03
**Success Criteria**:
1. Unified API key management logic.
2. Keys loaded cleanly without unnecessary complexity.

### Phase 3: Cloud Fallback
**Goal:** Implement Gemini -> OpenRouter -> Groq chain
**Requirements:** CLOUD-01, CLOUD-02, CLOUD-03
**Success Criteria**:
1. Initial request goes to Gemini.
2. If Gemini fails, request routes to OpenRouter.
3. If OpenRouter fails, request routes to Groq.

### Phase 4: Audit & Fix
**Goal:** Audit code for bugs and fix them
**Requirements:** TEST-02
**Success Criteria**:
1. Known bugs resolved and edge cases handled.

### Phase 5: Testing
**Goal:** Add tests and harden code
**Requirements:** TEST-01
**Success Criteria**:
1. Unit tests pass.
2. Integration tests for fallback chain pass.
