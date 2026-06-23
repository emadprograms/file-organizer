---
phase: 05
reviewers: [codex]
reviewed_at: 2026-06-23T22:05:00Z
plans_reviewed: [05-PLAN.md]
---

# Cross-AI Plan Review — Phase 05

## Codex Review

**Summary**
The updated Phase 05 plan effectively incorporates fixes for the previous concerns regarding error swallowing, hardcoded fallback values, and sorting criteria. The plan ensures robustness by passing context properly during fallback and updating the roadmap. However, two new critical risks have been introduced regarding how Arabic names are matched and how blank pages are detected in a vision-based pipeline. Additionally, the previous HIGH concerns remain partially resolved until the planned code is actually verified.

**Strengths**
- JIT directory creation correctly prevents filesystem clutter.
- Explicit instructions for the LLM to retain non-primary identities (Task 4) prevent entity loss.
- Fallback logic now successfully plans to inherit `house_number` from the batch context, protecting document routing (Task 5).
- Catching specific `LLMFailureError` instead of broad exceptions ensures structural code bugs won't be silently masked (Task 5).

**Concerns**
- **HIGH:** (NEW) Task 6 suggests a pre-check for completely blank pages before the LLM. Since the pipeline uses direct LLM vision for scanned documents (no prior OCR, as stated in `PROJECT.md`), any pre-check based on PDF text extraction (like PyMuPDF's `get_text()`) will falsely identify all scanned pages as blank, completely breaking the pipeline by skipping valid documents.
- **HIGH:** (NEW) Task 1 completely removes `.replace("ال", "")` and relies solely on exact word intersection. In Arabic, "ال" (the) is frequently added or omitted in informal writing. If a 2-word name like "محمد السالم" is written as "محمد سالم", exact intersection yields only 1 matched word, which will fail a typical 2-word threshold, causing the pipeline to miss the resident entirely. A more robust normalizer is needed rather than pure exact matching.
- **HIGH:** (PARTIALLY RESOLVED) Catching a broad `Exception` in `process_single_page` (Task 5). The fix is planned but not yet implemented/verified.
- **HIGH:** (PARTIALLY RESOLVED) The fallback classification drops the `house_number` and hardcodes `"UNKNOWN"` (Task 5). The fix is planned but not yet implemented/verified.

**Suggestions**
- **For Task 6:** If a blank page pre-check is implemented, it must use image analysis (e.g., checking for high variance/non-white pixels or file size thresholds) rather than text extraction, since the PDFs are scans.
- **For Task 1:** Instead of just exact string intersection, implement an Arabic-aware comparison that safely normalizes the "ال" prefix (e.g., stripping it only if it's at the start of the word) to allow "السالم" to match "سالم".
- **For Previous HIGHs:** Proceed with executing Task 5 as planned to fully resolve the exception swallowing and fallback logic.

**Risk Assessment**
HIGH. While previous pipeline failures are addressed in the plan, the new "blank page" pre-check poses a severe risk of dropping all scanned documents if implemented via standard text extraction. Additionally, the strict Arabic name intersection will result in a high rate of missed residents.

---

## Consensus Summary

### Agreed Strengths
- Improved fallback routing logic protects document assignments.
- Specific exception handling prevents masked bugs.

### Agreed Concerns
- Blank page pre-check risks dropping all scanned images if using text extraction (HIGH).
- Exact word intersection for Arabic names will fail on common "ال" variations (HIGH).
- Previous exception swallowing and fallback bugs remain a risk until Task 5 code is verified (HIGH).

### Divergent Views
- None (single reviewer).
