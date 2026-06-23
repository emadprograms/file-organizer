# Milestone v1.1 Roadmap

**Phase 3: API Key Cycling & Telemetry**
- **Goal:** Implement robust key cycling across 45 keys and diagnostic telemetry.
- **Requirements:** HARD-01, HARD-03
- **Success Criteria:**
  1. System can cycle through all 45 API keys without dropping requests.
  2. Capacity per key is tracked and preemptively managed.
  3. Diagnostic logs clearly distinguish between token exhaustion and request limits.

**Phase 4: Precise Timing & Concurrency Tuning**
- **Goal:** Engineer request pacing and safely process long (90+ page) documents.
- **Requirements:** HARD-02, HARD-04
- **Success Criteria:**
  1. System natively avoids rate limits through mathematically spaced request timing.
  2. Documents exceeding 90 pages are processed completely without failure or progress loss.

**Phase 5: Generation Accuracy Refinement**
- **Goal:** Improve the accuracy of AI-generated categorization for house files.
- **Requirements:** ACC-01
- **Success Criteria:**
  1. AI accurately extracts and categorizes output into the exact 13-category folder structure with zero Hallucinations.
  2. Categorization logic is tuned to better handle complex Arabic resident edge cases.
