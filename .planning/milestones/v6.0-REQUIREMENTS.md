# Requirements for v6.0: LLM Accuracy & Evaluation

## 1. OCR Golden Data Pre-processing (REQ-01)
**Problem:** Uploading multi-megabyte PDFs to Gemini on every evaluation run is extremely slow and hits rate limits quickly.
**Requirement:** 
- A one-time Phase 62 script that extracts the `raw_dump.json` (OCR layer) for all 4 Golden PDFs using Gemini.
- Must rotate through 4 distinct API keys from `.env` and `.env2` to prevent throttling.
- Save the resulting JSON files directly to `tests/golden_data/`.

## 2. Automated Evaluation Harness (REQ-02)
**Problem:** We cannot optimize non-deterministic LLM prompts without a fast, reliable feedback loop.
**Requirement:** 
- A test script (`run_eval.py`) that executes the pipeline on the pre-processed `raw_dump.json` files for the 4 Golden PDFs.
- The script must programmatically compare the pipeline's output to the Golden YAML datasets.
- It must generate a scoreboard showing the accuracy percentage for Canonicalization, Grouping, and Routing to guide prompt engineering.

## 3. Name Canonicalization Accuracy (REQ-03)
**Problem:** The system creates random/duplicate folders because it fails to map extracted names (e.g., "Abdullah Mehmood") to the exact key in `tenants.yaml` (e.g., "Abdullah Hamid Mahmoud").
**Requirement:** 
- Tweak prompts and extraction logic using Gemma-4-31B to achieve **100% accuracy** in name canonicalization.
- The pipeline must output exactly the number of tenants specified in the Golden YAML. No hallucinated or extraneous folders are allowed.

## 4. Grouping Logic Accuracy (REQ-04)
**Problem:** Pages that belong together are split, and unrelated pages are merged.
**Requirement:** 
- Recursively optimize the LLM grouping prompts.
- Target **95%+ accuracy** in identifying correct document boundaries. If LLM reasoning limits are hit, a fallback to a minimum of 85% is acceptable.

## 5. Routing Logic Accuracy (REQ-05)
**Problem:** The overarching logic incorrectly routes grouped documents.
**Requirement:** 
- Maximize the final routing accuracy so that categorized documents map correctly to their intended physical structure.
