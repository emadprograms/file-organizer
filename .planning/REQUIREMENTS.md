## Milestone v1.1 Requirements

### API Hardening & Key Management
- [ ] **HARD-01**: Implement highly robust API key cycling across 45 keys, tracking capacity per key and switching preemptively or on specific error codes.
- [ ] **HARD-02**: Engineer precise request timing and spacing to avoid triggering rate limits natively, rather than just reacting to them via backoff.
- [ ] **HARD-03**: Add diagnostic capabilities to identify *why* a rate limit is happening (e.g. token bucket exhaustion vs request limits).
- [ ] **HARD-04**: Safely process long documents (90+ pages) without failure, leveraging the new key cycling and precise concurrency tuning.

### Output Accuracy
- [ ] **ACC-01**: Refine AI generation logic to improve the categorization accuracy of the final generated house files.

## Future Requirements
*(None)*

## Out of Scope
*(None)*

## Traceability
*(To be filled by roadmap)*
