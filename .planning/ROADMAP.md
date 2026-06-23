# Milestone v1.1 Roadmap

## Phase 3: API Key Cycling & Telemetry

- **Goal:** Implement robust key cycling across 45 keys, diagnostic telemetry, and IP-level rate limit hardening.
- **Requirements:** HARD-01, HARD-03
- **Success Criteria:**
  1. System can cycle through all 45 API keys without dropping requests.
  2. Capacity per key is tracked and preemptively managed.
  3. Diagnostic logs clearly distinguish between token exhaustion and request limits.
  4. Global IP-level RPM cap of 15 is enforced across all keys.
  5. All API calls (including retries) route through the rate limiter.
  6. Invalid responses fail gracefully after 2 attempts with a fallback classification.

## Phase 4: Precise Timing, Output Refinement & Concurrency Tuning

- **Goal:** Safely process long documents without bottlenecks, and ensure 100% accurate, clutter-free directory outputs.
- **Requirements:** HARD-02, HARD-04, OUT-01
- **Success Criteria:**
  1. **Concurrency & Timing:** System natively avoids rate limits through spaced timing. Progressive caching I/O bottleneck is resolved so threads aren't locked rewriting the cache file on every page.
  2. **Empty Folders:** Folders are generated dynamically on-write. Zero empty directories are created.
  3. **Fallback Folder:** Uncategorized/Unknown pages are explicitly dumped into a `Manual_Review` fallback folder instead of being forced into "General Letters" or dropped.
  4. **Schema Optimization:** The `house_number` field is removed from the AI prompt and Pydantic schema to save tokens, as the pipeline relies strictly on filename extraction.
  5. **Safe Data Handling:** `shutil.rmtree` destructive wipes of entire house directories are removed to prevent data loss. `shutil.copy2` duplicating massive original PDFs is removed to save disk space.
  6. **Identity Preservation:** The `resolve_entities` LLM prompt correctly retains non-primary family member identities instead of mapping wives/children to the primary tenant and erasing them.
  7. **Reliable LLM Retries:** Silent failures on LLM retries (bare `except Exception: pass`) are fixed so errors are handled/logged properly. The `other_letters` category is removed from `NONE_EXPECTED_CATEGORIES` to ensure lazy extractions are retried instead of accepted blindly.
  8. **Precise Document Grouping:** The pipeline correctly separates distinct documents by enforcing strict date-matching during grouping, stopping pages with different dates from fusing. Non-anchor documents properly respect the extracted recipient's name instead of being forced into the primary tenant's timeline.

## Phase 5: Generation Accuracy Refinement

- **Goal:** Improve the accuracy of AI-generated categorization for house files.
- **Requirements:** ACC-01
- **Success Criteria:**
  1. AI accurately extracts and categorizes output into the exact 13-category folder structure with zero Hallucinations.
  2. Categorization logic is tuned to better handle complex Arabic resident edge cases.
