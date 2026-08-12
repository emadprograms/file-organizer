# Phase 66: OCR Letter Continuation Detection (is_continuation) Plan

## Goal
Implement the `is_continuation` fix for the OCR pass so that pages lacking subjects/addressees are correctly marked as continuations of the previous page.

## Details
1. **Update Schema:**
   - In `src/core/models.py`, add `is_continuation: bool = False` to `PageData`.

2. **Update OCR Prompt / Config:**
   - Modify the OCR prompt configuration (e.g. `src/llm/prompts.py` or similar) to instruct the AI:
     "If a page classified as a 'letter' lacks a subject line (الموضوع), addressee line (إلى/سعادة), or new reference number, it is likely a continuation of the previous page. Set `is_continuation: true` and leave sender, receiver, and subject null."

3. **Writing Tests:**
   - Write rigorous unit tests to verify the `is_continuation` logic is properly handled by the schema and prompt structure.

## Execution Steps
1. Modify `PageData` in `src/core/models.py`.
2. Locate the OCR prompt and modify it to include the `is_continuation` instruction.
3. Write test in `tests/test_ocr_continuation.py` or similar to verify prompt structure and schema.
4. Run tests and debug if necessary.
