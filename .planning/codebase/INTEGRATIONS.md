---
last_mapped_commit: HEAD
---
# Integrations

**Focus:** tech
**Date:** 2026-06-26

## External APIs and Services
- **Gemini API**: Used via `google-genai` for cloud LLM inference.
- **OpenAI API**: Used via `openai` package for fallback/secondary LLM inference.
- **Local Fallback Models**: Uses local Qwen-VL or similar local models when cloud rate limits are hit or offline mode is requested (`--no-local` flag logic).

## Platform-Specific Integrations
- **macOS Vision Framework**: In `src/pipeline.py`, the code uses macOS native `Vision` and `Quartz` frameworks via PyObjC to perform local OCR if running on Darwin.
