# Phase 1 Validation Strategy

**Phase**: 1 (ocr-pdf-pipeline)
**Date**: 2026-06-21

## 1. Goal
Ensure the PyMuPDF ingestion and rendering pipeline correctly reads large Arabic PDFs, safely extracts pages into images without exceeding memory limits, and successfully formats the payloads for the LLM without data loss.

## 2. Core Validation Axes
- **Memory & Concurrency**: Validate that processing a 200-page document uses bounded memory (e.g., max 5 active threads rendering/holding images).
- **Quality**: Validate the output images have sufficient resolution (e.g., 150 DPI) for legible text extraction.
- **Error Handling**: Validate that the pipeline retries upon API rate limit (429) errors without dropping pages.
- **Sequence Reconstruction**: Validate that after parallel processing, the sequential re-assembly correctly orders pages 1 through 200.

## 3. Required Test Cases
- [ ] Ingest a 5-page PDF and verify 5 valid image bytes objects are created.
- [ ] Simulate an API failure on page 3 and verify the retry logic eventually succeeds.
- [ ] Monitor memory usage on a large dummy PDF to ensure concurrency constraints hold.

## 4. Verification Methods
- Unit tests using `pytest` to mock the PyMuPDF document and `ThreadPoolExecutor`.
- Manual verification: Run the pipeline headlessly on a real sample document with the LLM API mocked, checking log outputs for the correct retry sequences.
