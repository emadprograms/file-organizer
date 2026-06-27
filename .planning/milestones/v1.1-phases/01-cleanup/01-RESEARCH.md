# Phase 01 Research: Cleanup

## What to Plan For

To completely remove local model support and redundant legacy code paths in accordance with **REF-01** and **REF-02**, we must address changes across several files. 

### 1. `src/llm.py`
This file contains the majority of the local model logic.
*   **Remove `use_local_llm` parameter** from the `GemmaClient.__init__` signature and assignment.
*   **Remove environment variable parsing** for local models (`LOCAL_BASE_URL`, `LOCAL_MODEL_NAME`, `LOCAL_TEXT_MODEL_NAME`, `USE_LOCAL_LLM`).
*   **Remove initialization of `self.local_client`** (the OpenAI client pointing to Ollama).
*   **Delete the `should_use_local_fallback` method**.
*   **Delete `extract_page`**: This method explicitly uses `qwen2.5vl:7b` to transcribe text from images.
*   **Delete `classify_extracted_page`**: This method explicitly uses `qwen2.5:14b` to classify extracted text.
*   **Update `classify_page_direct`**: Remove the ternary logic for `attempts` (`attempts = 1 if self.use_local_llm else 100`) and replace it with a fixed fallback or max attempts.
*   **Update `check_bulk_semantic_grouping`**: Completely remove the `if use_local:` fallback block and related variables. Retain only the cloud logic path using `gemma-4-26b-a4b-it`. 
*   **Cleanup imports**: Remove `openai` if it is no longer used anywhere else.

### 2. `src/pipeline.py`
This file contains the pipeline logic that orchestrates the local fallback.
*   **Remove `use_local_llm` parameter** from `Pipeline.__init__` and its passage to `GemmaClient`.
*   **Remove the `deferred_local_pages` list** and the entire **"Phase 2: Run deferred local classification (Pass 1b)"** block at the end of the extraction loop.
*   **Remove the text caching logic** (`text_cache` / `.extracted.cache.json`) since text extraction was only used for the local Qwen-14B classification.
*   **Remove local fallback logic** in the extraction loop (`use_local = self.client.should_use_local_fallback()`, and the subsequent `if use_local:` extraction block). The direct cloud classification should just fail or wait via rate limits (which `_route_llm_call` handles).

### 3. `src/main.py`
*   **Remove the `--no-local` CLI argument** from `argparse`.
*   **Remove the `USE_LOCAL_LLM` environment variable parsing**.
*   **Remove `use_local_llm=final_use_local`** when instantiating the `Pipeline`.

### 4. Configuration (`.env` and `.env.example`)
*   Remove `LOCAL_BASE_URL`
*   Remove `LOCAL_MODEL_NAME`
*   Remove `LOCAL_TEXT_MODEL_NAME`
*   Remove `USE_LOCAL_LLM`

### 5. Scripts (Legacy Code Paths)
Several scripts in the `scripts/` directory are explicitly for evaluating or testing local models. These should be deleted:
*   `scripts/evaluate_local.py`
*   `scripts/test_local_qwen.py`

*(Note: There are other scripts like `test_openrouter_stress.py` and `compare_groq_models.py` which are likely part of upcoming Cloud fallbacks. Leave those alone unless explicitly told otherwise).*
