# Phase 02 Discussion Log

**Date:** 2026-06-27

### Key Management Scope
- **Options presented:** Strip down to a single GEMINI_API_KEY vs keep multi-key logic.
- **User selected:** Strip down to a single key.
- **Notes:** Use one key, make a folder with a permanent file to track successful calls in last 24 hours (1500 limit). Enforce a 7-second minimum per call. 65s wait on 429. 15s wait on 5xx. Pages process sequentially. Inform user of remaining quota on startup.

### Environment Configuration
- **Options presented:** Centralize key loading in `config.py` vs load inside modules.
- **User selected:** Centralize key loading in `config.py`.
- **Notes:** Create a central config.py to load and validate all keys (Gemini, Groq, OpenRouter) at startup.

### Missing Keys Behavior
- **Options presented:** Fail fast vs Lazy fallback.
- **User selected:** Fail fast.
- **Notes:** Require all keys at startup for cleaner downstream code.
