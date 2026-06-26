---
last_mapped_commit: HEAD
---
# Codebase Concerns

**Focus:** concerns
**Date:** 2026-06-26

## Technical Debt & Fragility
- **Platform Coupling**: `src/pipeline.py` contains macOS-specific imports (`Vision`, `Quartz` via `PyObjC`). This will crash or behave differently on Linux/Windows if the `sys.platform == "darwin"` check is ever bypassed, or if dependencies are missing.
- **Complex Pipeline Logic**: `src/pipeline.py` has heavily nested logic in `process_pdf`, handling Cloud LLM, Local fallback, cache lookups, and macOS OCR all in one large method. This could be refactored into strategies or smaller methods.
- **Concurrency Risks**: `SimpleCache` relies on atomic file renames (`os.replace`) and a `threading.Lock`, which works for threads but will fail to prevent race conditions if multiple *processes* run simultaneously.

## Security
- API Keys are passed around via `.env` and `GEMINI_API_KEYS`. Must ensure these aren't accidentally logged or cached in the `.cache.json` files.
