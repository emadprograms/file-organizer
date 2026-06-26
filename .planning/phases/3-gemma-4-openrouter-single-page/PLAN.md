# Phase 3: Gemma 4 OpenRouter Single Page Test

## Goal
Verify that the OpenRouter API key can successfully handle a single-page classification request using Gemma 4 (26B), mirroring the logic used in `scratch/benchmark_gemma_local_vs_cloud.py` but focusing exclusively on the cloud model.

## Context
- Previous phase confirmed OpenRouter connectivity.
- We want to test the model's ability to process a real page image from the dataset.
- The test should allow the user to specify a PDF file number and page number.

## Plan
1. **Create a test script**: 
   - Base it on `scratch/benchmark_gemma_local_vs_cloud.py`.
   - Remove the local model benchmarking logic.
   - Ensure it uses `GemmaClient` with `use_local_llm=False` (which defaults to OpenRouter/Cloud).
   - Target model: `gemma-4-26b-a4b-it`.
   - Maintain the same system prompt and JSON output constraints.
2. **Execute the script**:
   - Run the script with a sample PDF and page.
   - Verify the response is valid JSON and contains the expected fields.
3. **Validate**:
   - Confirm the request completes without errors (e.g., 429, 401, etc.).

## Success Criteria
- The script successfully classifies a page and prints the result.
- No API errors are encountered during the process.
