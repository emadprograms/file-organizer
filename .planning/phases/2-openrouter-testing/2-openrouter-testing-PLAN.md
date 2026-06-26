# Phase 2: OpenRouter Integration & Testing Plan

**User Story:**
As a developer, **I want to** verify that my OpenRouter API key works with the Gemma 4 26B model **so that** I can reliably use it for high-quality document classification.

## Requirements
- [OPENROUTER-01]: Successful API communication with OpenRouter using Gemma 4 26B.

## Tasks
- [x] **Task 1: Create OpenRouter Test Script**
    - Create a standalone script `scripts/test_openrouter.py` that loads `OPENROUTER_API_KEY` from `.env`.
    - Use the `openai` library to send a simple prompt to `google/gemma-4-26b-a4b-it:free`.
    - Print the response and latency.
- [x] **Task 2: Execute Connectivity Test**
    - Run the script and verify a successful response.
    - Validate that the `.env` loading works as expected.
- [ ] **Task 3: Document Results**
    - Record the success/failure and any latency observations in the phase summary.

## Verification Strategy
- **Verification 1:** Run `python scripts/test_openrouter.py`. Success is defined as receiving a coherent text response from the model.
- **Verification 2:** Check that no API keys are hardcoded in the script.
