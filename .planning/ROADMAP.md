# Roadmap: v1.1 Code Hardening and Tech Debt Cleanup

## Proposed Roadmap

**2 phases** | **4 requirements mapped** | All covered ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 4 | Legacy Logic Porting & Verification | Replicate the existing Bahrain housing logic via external config scripts. | REF-04 | 2 |
| 5 | Decouple Core Pipeline | 1/1 | Complete   | 2026-07-02 |

### Phase Details

### Phase 4: Legacy Logic Porting & Verification (COMPLETED)

Goal: Replicate the existing Bahrain housing logic via external config scripts.
Requirements: REF-04
Success criteria:

1. The extracted logic is ported into default fallback scripts provided to the user.
2. The config accurately represents the old hardcoded structure.

### Phase 5: Decouple Core Pipeline

Goal: Remove all hardcoded domain logic from the core pipeline engine and verify via the scripts from Phase 4.
Requirements: REF-01, REF-02, REF-03
Success criteria:

1. `src/llm.py` contains no Bahrain housing specific prompts.
2. `src/organizer.py` relies strictly on YAML-defined rules.
3. `src/pipeline.py` no longer contains real-estate specific heuristics.
4. A test execution of the pipeline completes successfully, proving backward compatibility.
