---
wave: 1
depends_on: []
files_modified:
  - src/llm.py
  - src/pipeline.py
  - src/main.py
  - scripts/evaluate_local.py
  - scripts/test_local_qwen.py
  - .env
  - .env.example
autonomous: true
---

# Phase 1: Cleanup

## Goal
Remove local model support and redundant code

## Requirements
- REF-01
- REF-02

## Tasks

### Wave 1: Delete Local Legacy Scripts

```xml
<task>
  <read_first>
    - scripts/
  </read_first>
  <action>
    Delete the following files:
    - `scripts/evaluate_local.py`
    - `scripts/test_local_qwen.py`
  </action>
  <acceptance_criteria>
    - `ls scripts/evaluate_local.py` returns a non-zero exit code (file does not exist).
    - `ls scripts/test_local_qwen.py` returns a non-zero exit code (file does not exist).
  </acceptance_criteria>
</task>
```

### Wave 2: Remove Local LLM logic from Codebase

```xml
<task>
  <read_first>
    - src/llm.py
    - src/pipeline.py
    - src/main.py
    - .env.example
  </read_first>
  <action>
    Update `src/llm.py`:
    - Remove `import openai`.
    - In `GemmaClient.__init__`: Remove `use_local_llm` parameter and `self.use_local_llm` assignment. Remove initialization of `local_base_url` and `self.local_client`.
    - Delete `should_use_local_fallback`, `extract_page`, and `classify_extracted_page` methods.
    - In `classify_page_direct`: Replace `attempts = 1 if self.use_local_llm else 100` with `attempts = 100`.
    - In `check_bulk_semantic_grouping`: Remove all references to `use_local`. Run the cloud logic unconditionally. In the `except Exception as e` block, remove `use_local = True` and replace the local fallback block with `raise`.
    
    Update `src/pipeline.py`:
    - In `Pipeline.__init__`: Remove `use_local_llm` parameter and stop passing it to `GemmaClient`.
    - In `process_pdf`:
      - Remove `text_cache` initialization and the `text_cache` check block.
      - Remove `deferred_local_pages` list.
      - Remove `use_local = self.client.should_use_local_fallback()` logic.
      - Execute the cloud logic (currently `if not use_local:`) unconditionally.
      - In the `except Exception as e:` block for cloud classification, instead of setting `use_local = True`, write the fallback `PageClassification` (with `OTHER_LETTERS` / `UNKNOWN`) to `pages_cache` and append to `raw_pages` (using `self._get_fallback_house_number(pages_cache)`).
      - Remove the `if use_local:` local vision extraction block.
      - Remove the entire "Phase 2: Run deferred local classification" block.
    
    Update `src/main.py`:
    - Remove `parser.add_argument("--no-local", ...)` from the CLI.
    - Remove `env_use_local` and `final_use_local` definitions.
    - Instantiate `Pipeline` without the `use_local_llm` argument.
    
    Update `.env` (if exists) and `.env.example`:
    - Delete `LOCAL_BASE_URL`, `LOCAL_MODEL_NAME`, `LOCAL_TEXT_MODEL_NAME`, and `USE_LOCAL_LLM`.
  </action>
  <acceptance_criteria>
    - `grep -q "use_local_llm" src/llm.py` returns a non-zero exit code (fails).
    - `grep -q "import openai" src/llm.py` returns a non-zero exit code.
    - `grep -q "extract_page(" src/llm.py` returns a non-zero exit code.
    - `grep -q "classify_extracted_page(" src/llm.py` returns a non-zero exit code.
    - `grep -q "use_local_llm" src/pipeline.py` returns a non-zero exit code.
    - `grep -q "deferred_local_pages" src/pipeline.py` returns a non-zero exit code.
    - `grep -q "no-local" src/main.py` returns a non-zero exit code.
    - `python src/main.py -h` runs successfully without any errors or mentioning `--no-local`.
  </acceptance_criteria>
</task>
```

## Verify
- `python src/main.py -h` shows no `--no-local` argument.
- `rg "use_local_llm" src/` returns no results.

## must_haves
```yaml
truths:
  - "The codebase contains no references to `use_local_llm`."
  - "The codebase contains no references to `openai` package."
  - "The `Pipeline` does not instantiate or track deferred pages for local execution."
  - "`GemmaClient` classification methods run strictly against the cloud models."
prohibitions: []
```

## Artifacts this phase produces
- None
