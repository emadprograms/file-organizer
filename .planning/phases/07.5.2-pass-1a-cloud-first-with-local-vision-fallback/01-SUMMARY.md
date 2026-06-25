# Phase 07.5.2: Pass 1a Cloud-First Vision Extraction with Local Fallback - Summary

## Outcome
The hybrid pipeline architecture has been successfully implemented and verified. The system now prioritizes direct cloud classification using `gemma-4-26b-a4b-it` and seamlessly falls back to local `qwen2.5vl:7b` for text extraction when rate limits are active, deferring text reasoning to `qwen2.5:14b` at the end of the run. 

## Work Completed
- **`src/llm.py`:** Enforced global IP rate limit (`15 RPM`). Exposed `should_use_local_fallback()`, `activate_cooldown()`, and implemented the cloud-direct `classify_page_direct()` method.
- **`src/pipeline.py`:** Integrated the hybrid routing logic into `process_pdf`. Local fallbacks are now queued in `deferred_local_pages` and processed in Pass 1b at the end of the file extraction loop, completely eliminating mid-loop model memory swapping penalties.
- **Tests:** Added new unit tests covering global RPM enforcement, fallback logic, and timeout/resumption flows.

## Metrics
- **Performance:** Cloud calls average ~5-8s sequentially. The hybrid split maintains optimal throughput (~7s/page avg) even when the pipeline hits the 15 RPM cooldown window, gracefully using the 65s cooldown time to process local OCR.
- **Test Coverage:** All unit tests in `test_llm.py` successfully pass.
