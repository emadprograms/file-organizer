# Phase 1: OCR & PDF Pipeline - UAT

## Test Cases

### 1. E2E Pipeline Execution
- **Action**: Place a `sample.pdf` in the root of the workspace, configure the `.env` file with `GEMINI_API_KEYS`, and run `python src/main.py`.
### Result: Partially Passed

- Pipeline code executes correctly and correctly extracts the first several pages.
- **Limitation Discovered**: Aggressive API rate-limiting blocks most requests when `max_workers` is too high, leading to `ClientError` (429 Too Many Requests). The script's `max_workers` has been tuned down to 3, but the free-tier Gemini limits may still periodically rate limit the application.
- Fallback/Wait logic with `tenacity` tries to mitigate this, but `httpx` drops connections if limits are hit too fast.
- **Expected Result**: 
  - The script successfully runs and extracts images from the PDF.
  - The script sends the images to the Gemma API (or the standard gemini-1.5-flash endpoint).
  - The documents are correctly categorized and split into individual PDF files.
- **Status**: Pending

### 2. Multi-Key Fallback & Concurrency (Optional / Advanced)
- **Action**: Provide multiple comma-separated keys in `GEMINI_API_KEYS` and test with a large PDF.
- **Expected Result**: 
  - `ThreadPoolExecutor` spins up multiple workers.
  - When a rate limit exception is simulated or hit, it falls back to the next key automatically.
- **Status**: Pending
