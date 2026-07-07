# Codebase Concerns

**Analysis Date:** 2026-07-07

## Tech Debt

**LLM Routing Logic:**
- Issue: The `_route_llm_call` method in `src/llm/llm.py` is becoming a "god method" that handles routing, retries, failovers, trace logging, and custom error parsing in one place.
- Files: `src/llm/llm.py`
- Impact: Harder to test and maintain as new providers or routing strategies are added.
- Fix approach: Extract retry logic into a decorator or a separate `RetryHandler` class.

**Direct-to-PDF Logic in Organizer:**
- Issue: `src/processing/organizer.py` (implied by `src/organize.py` usage) mixes high-level organization logic with low-level PDF splitting using `fitz`.
- Files: `src/processing/organizer.py`
- Impact: Tightly couples the business logic of "where to put the file" with the technical implementation of "how to split a PDF".
- Fix approach: Create a `PDFService` abstraction to handle all `fitz` operations.

## Known Bugs

**Arabic Terminal Rendering:**
- Symptoms: Arabic characters may not render correctly in some Windows terminals during dry runs.
- Files: `src/organize.py`
- Trigger: Running with `--dry-run` on Windows without UTF-8 encoding configured.
- Workaround: Set `PYTHONIOENCODING=utf8`.

## Security Considerations

**API Key Management:**
- Risk: API keys are loaded from `.env` and passed around. If `verbose` logging is too aggressive, keys could potentially be leaked in logs (though not currently observed).
- Files: `src/llm/llm.py`, `.env`
- Current mitigation: Keys are kept in environment variables and not hardcoded.
- Recommendations: Implement a masking utility for sensitive strings in the logger.

## Performance Bottlenecks

**Sequential API Calls:**
- Problem: The pipeline processes pages in a largely sequential manner to avoid rate limits.
- Files: `src/processing/pipeline.py`, `src/llm/llm.py`
- Cause: Reliance on LLM APIs with strict quotas.
- Improvement path: Implement a more sophisticated request queue with per-provider rate limit tracking to maximize concurrency.

**PDF Processing Speed:**
- Problem: Reading and splitting large PDFs can be slow.
- Files: `src/processing/organizer.py`
- Cause: PyMuPDF's sequential processing of large files.
- Improvement path: Use multiprocessing for PDF splitting across different document groups.

## Fragile Areas

**Boundary Detection:**
- Files: `src/processing/grouping.py`
- Why fragile: Relies on LLM prompts to correctly identify the "start" and "end" of documents. Slight changes in LLM behavior or prompt wording can shift boundaries.
- Safe modification: Always update `tests/test_grouping.py` with new "golden" examples when changing prompts.
- Test coverage: Good, but requires high-quality fixtures.

## Scaling Limits

**Memory Usage:**
- Current capacity: Works well for hundreds of pages.
- Limit: Since the pipeline loads `PageData` objects into memory and passes them as lists, very large documents (thousands of pages) might cause high memory pressure.
- Scaling path: Use a generator-based approach for page processing instead of loading all pages into a list.

## Dependencies at Risk

**Google GenAI SDK:**
- Risk: The `google-genai` SDK is relatively new and subject to breaking changes.
- Impact: Breaking changes would require updates to `src/llm/providers.py`.
- Migration plan: The `LLMProvider` abstraction already mitigates this by isolating provider-specific code.

## Missing Critical Features

**GUI/Web Interface:**
- Problem: Currently a CLI tool. Non-technical users cannot use it.
- Blocks: Broad adoption.

**Advanced Validation:**
- Problem: No way to manually "verify" or "correct" LLM grouping before physical PDF splitting occurs.
- Blocks: Perfect accuracy for critical documents.

## Test Coverage Gaps

**Edge Case PDFs:**
- What's not tested: PDFs with corrupted pages, extremely large images, or mixed-language content that doesn't fit the standard patterns.
- Files: `src/processing/organizer.py`
- Risk: The organizer might crash on malformed PDFs.
- Priority: Medium.

---

*Concerns audit: 2026-07-07*
