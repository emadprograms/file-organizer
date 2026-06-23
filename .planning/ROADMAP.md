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
  9. **Arabic String Safety:** The destructive `.replace("ال", "")` logic is removed or refactored so it does not carve letters out of the middle of Arabic names (e.g., destroying "خالد" into "خاد"), preventing random timeline splits.
  10. **Prefix Document Rescue:** The timeline initialization logic is fixed so that `PERSONAL_DETAILS` (ID cards) and other perfectly valid documents appearing at the front of a scanned dossier can initialize a timeline or be properly assigned, instead of being permanently orphaned to "UNKNOWN".
  11. **Family Size Resilience:** The timeline logic is fixed to allow Anchor documents (Contracts/Basic Details) containing more than 3 names to establish a timeline, preventing large families from being orphaned.
  12. **Accurate Name Matching:** The `< 2` word intersection threshold is adjusted to handle perfectly valid single-word Arabic names (e.g., "محمد") so they aren't forcibly split into duplicate resident folders.
  13. **Array Order Independence:** Anchor documents with multiple names (e.g., Husband and Wife) will correctly map to the timeline regardless of which name the AI output first in the array, preventing immediate timeline hijacking.
  14. **Atomic Cache Saving:** The cache file is written atomically (write to temp file, then rename) to prevent total data corruption and truncation if the program crashes or is stopped midway.
  15. **GUI Performance:** The `poll_telemetry` UI update loop is optimized to only render the latest state rather than re-rendering every intermediate state, preventing complete UI freezing.
  16. **Folder Sorting:** Numbered output folders (`1.`, `2.`, etc.) are zero-padded (e.g., `01.`) so Windows Explorer sorts them correctly instead of `1, 10, 11, 2...`, preserving the chronological flow.

## Phase 5: Generation Accuracy Refinement

- **Goal:** Improve the accuracy of AI-generated categorization for house files.
- **Requirements:** ACC-01
- **Success Criteria:**
  1. AI accurately extracts and categorizes output into the exact 13-category folder structure with zero Hallucinations.
  2. Categorization logic is tuned to better handle complex Arabic resident edge cases.
