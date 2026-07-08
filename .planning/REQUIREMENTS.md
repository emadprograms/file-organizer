# Milestone v1.2 Requirements

### Anti-Hallucination Schema Enforcement
- [ ] **SCHM-01**: Replace generic string typing in RoutingResponse with a strict Pydantic Literal binding exactly to the allowed folders.

### "True Until Proven Guilty" Grouping Logic
- [ ] **PRMPT-01**: Update the grouping prompt to explicitly enforce "True Until Proven Guilty" for document boundaries.
- [ ] **PRMPT-02**: Instruct the LLM that letters are assumed to be continuations unless the topics are vastly different.
- [ ] **PRMPT-03**: Add explicit rules and examples for handling implicit continuations like un-headered tables and appendices.

### Rate Limiting & Router Safety Net
- [ ] **RES-01**: The tenacity retry predicate must accept the Exception object so rate limiting waits out the 60s cooldown instead of crashing instantly.
- [ ] **RES-02**: The router must allow critical rate limit and runtime errors to bubble up to halt the pipeline.
- [ ] **RES-03**: Remove the global consecutive routing failures permanent lockout in the router.

### Chunk State Management
- [ ] **GRP-01**: Decrease grouping chunk sizes to [5, 3, 2] and set consecutive failures limit to 3.
- [ ] **GRP-02**: Ensure the chunk size index is properly reset to 0 upon processing a successful chunk.
- [ ] **GRP-03**: Restructure the failure counter so that exhausting the chunk limit gracefully halts the pipeline instead of crashing blindly, enabling the checkpoint system.
- [ ] **GRP-04**: Prevent the overlap merging logic from blindly merging chunks mathematically; ensure it respects LLM boundaries.
