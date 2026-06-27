# Phase 02 Research: Key Mgmt

## Overview
This research covers the context and requirements for Phase 02, focusing on simplifying the API key loading and switching processes, and enforcing strict validation of environment configuration before the core application execution begins.

## Requirements
- **Goal:** Simplify API key loading and switching
- **Requirements Covered:** REF-03
- **Success Criteria:**
  1. Unified API key management logic.
  2. Keys loaded cleanly without unnecessary complexity.

## Execution Strategy
- Create a `config.py` module to centralize key loading and validation.
- Require `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, and `GROQ_API_KEY` to be present at startup.
- Implement a "fail fast" approach where the application halts immediately if any key is missing. This eliminates the need for downstream `None` checks.
- Set up a tracking directory and a permanent log file for successful API calls to enforce a limit of 1500 calls per 24 hours.
- Calculate and display the remaining quota upon startup.
- Enforce strict rate limiting: process pages sequentially, mandate a minimum of 7 seconds per call, wait 65 seconds on a `429` error, and wait 15 seconds on a `500` or `503` error.

## Validation Architecture
- **Nyquist Validation Readiness:** To ensure Nyquist can validate the system effectively, the `config.py` module provides strict boundaries and defined application state immediately upon launch.
- **Fail Fast Configuration:** The validation architecture ensures that no component of the application starts unless the environment configuration is perfectly established.
- **Quota Tracking Validation:** Continuous read/write validation against the permanent log file ensures that the 1500-call quota is respected accurately.

## References
- `.planning/phases/02-key-mgmt/02-CONTEXT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
