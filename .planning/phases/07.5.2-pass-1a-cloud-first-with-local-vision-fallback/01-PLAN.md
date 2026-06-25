---
wave: 1
depends_on: []
files_modified:
  - src/llm.py
  - src/pipeline.py
  - tests/test_llm.py
autonomous: true
requirements:
  - D-01
  - D-02
  - D-03
  - D-04
---

# Phase 07.5.2: Pass 1a Cloud-First Vision Extraction with Local Fallback - Plan

## Goal
Implement a hybrid pipeline where cloud calls directly classify pages (`Image -> PageClassification`) while respecting a strict 15 RPM global IP limit. When rate limits or cooldowns are active, the system runs local OCR (`qwen2.5vl:7b`) to extract text and defers local classification (`qwen2.5:14b`) to the end of the file to maximize speed and prevent RAM model-swapping.

## Tasks

```xml
<task>
  <read_first>
    - src/llm.py
    - .planning/phases/07.5.2-pass-1a-cloud-first-with-local-vision-fallback/07.5.2-CONTEXT.md
  </read_first>
  <action>
    In `src/llm.py`, clean up the global rate limit tracking and expose fallback methods:
    1. Set the global RPM limit to a strict 15 cap: `self.global_rpm_limit = 15` (independent of the number of API keys, to respect the IP rate limit).
    2. Expose a helper method `should_use_local_fallback(self) -> bool` that returns `True` if `time.time() < GemmaClient.global_cooldown_until` or `len(GemmaClient.global_rpm_tracker) >= self.global_rpm_limit`.
    3. Expose `activate_cooldown(self)` that sets `GemmaClient.global_cooldown_until = time.time() + 65.0` and saves the rate limit state.
    4. Implement `classify_page_direct(self, image_bytes: bytes, footer_text: str = None) -> PageClassification` which calls the cloud model `gemma-4-26b-a4b-it` using the standard `_route_llm_call` to perform direct classification.
  </action>
  <acceptance_criteria>
    `self.global_rpm_limit` is strictly set to 15.
    `should_use_local_fallback` correctly detects active cooldowns or maximum tracker counts.
    `classify_page_direct` exists and uses the cloud client to return a parsed `PageClassification`.
  </acceptance_criteria>
</task>

<task>
  <read_first>
    - src/pipeline.py
    - src/llm.py
  </read_first>
  <action>
    In `src/pipeline.py`, update `process_pdf` to implement the hybrid split pipeline:
    1. During the loop of pages to process:
       - If `self.client.should_use_local_fallback()` is `True`, run local OCR: call `self.client._extract_text_with_qwen(i_bytes)` and append `(p_idx, text, extracted_footer)` to a `deferred_local_pages` list.
       - If `False`, try direct cloud classification: call `self.client.classify_page_direct(i_bytes, extracted_footer)` and append the result to `raw_pages`.
       - If the cloud request raises an exception (e.g., transient error or 429), catch it, call `self.client.activate_cooldown()`, fall back to local OCR, and append to `deferred_local_pages`.
    2. After the page processing loop completes, if `deferred_local_pages` contains items:
       - Run local reasoning (Pass 1b): loop through `deferred_local_pages`, call `self.client.classify_extracted_page(text, footer)`, and append the results to `raw_pages`.
    3. Sort `raw_pages` by page index and verify all expected pages were recovered.
  </action>
  <acceptance_criteria>
    `process_pdf` successfully routes to cloud classification or local OCR fallback.
    `deferred_local_pages` holds pages processed locally during the loop.
    Pass 1b runs on all deferred pages at the very end of the loop.
    All tests run without page-loss assertion errors.
  </acceptance_criteria>
</task>

<task>
  <read_first>
    - tests/test_llm.py
  </read_first>
  <action>
    Update unit and integration tests in `tests/test_llm.py` to match the new class methods and pipeline architecture, ensuring rate limit tests check the strict 15 cap.
  </action>
  <acceptance_criteria>
    All unit and integration tests pass successfully.
  </acceptance_criteria>
</task>
```
