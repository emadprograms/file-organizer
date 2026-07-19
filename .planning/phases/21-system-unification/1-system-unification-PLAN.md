---
wave: 1
depends_on: []
files_modified:
  - requirements.txt
  - src/core/categories.yaml
  - src/core/schemas.py
  - src/llm/llm.py
  - src/llm/providers.py
  - src/pdf/image_processing.py
  - src/categorization.py
  - src/main.py
autonomous: true
---

# Phase 21: System Unification Plan

## Goal
Port file-categorizer logic for `_report.json` generation using Gemini 3.1 FL and OCR to the main repository.

## Requirements Covered
- CAT-01
- CAT-02

<threat_model>
ASVS Level: 1
Blocking Threshold: High
Threats:
- Potential path traversal if `target_dir` in `categorization.py` is manipulated (mitigated by strict type hinting and existing directory validation).
- File overwrite risks during JSON writes (mitigated by atomic write pattern).
- Arbitrary file uploads/reads from image extraction (mitigated by enforcing `.pdf` extension).
</threat_model>

## Tasks

### Wave 1: Requirements and Assets Porting

<task>
<description>Update dependencies and configuration</description>
<action>Update `requirements.txt` to include `opencv-python` and `numpy`. Copy `categories.yaml` from `../file-categorizer/categories.yaml` to `src/core/categories.yaml`.</action>
<read_first>
- requirements.txt
- ../file-categorizer/categories.yaml
</read_first>
<acceptance_criteria>
- `requirements.txt` contains `opencv-python` and `numpy`.
- `src/core/categories.yaml` exists and matches the source file.
</acceptance_criteria>
</task>

### Wave 2: Image Processing Porting

<task>
<description>Port OpenCV image processing pipeline</description>
<action>Create `src/pdf/image_processing.py` and port functions like `extract_and_clean_page`, `adjust_levels`, `auto_deskew`, and `process_pdf` exactly from `../file-categorizer/src/image_processing.py`.</action>
<read_first>
- ../file-categorizer/src/image_processing.py
- src/pdf/image_processing.py
</read_first>
<acceptance_criteria>
- `src/pdf/image_processing.py` contains the ported functions with OpenCV auto-deskew and illumination normalization intact.
- Function signatures match the original.
</acceptance_criteria>
</task>

### Wave 3: LLM and Schema Support

<task>
<description>Add Multimodal Support and Schemas</description>
<action>Modify `src/core/schemas.py` to add `CategorizationResult` Pydantic models mapping to `categories.yaml`. Update `src/llm/providers.py` (`GeminiProvider.generate`) and `src/llm/llm.py` to support multimodal inputs (passing images in the `contents` payload).</action>
<read_first>
- src/core/schemas.py
- src/llm/providers.py
- src/llm/llm.py
- ../file-categorizer/src/ai_classification.py
</read_first>
<acceptance_criteria>
- `CategorizationResult` is defined in `schemas.py`.
- `GeminiProvider.generate` successfully accepts list of contents containing image payloads.
</acceptance_criteria>
</task>

### Wave 4: Categorization Module

<task>
<description>Implement Categorization Logic with Bypass</description>
<action>Create `src/categorization.py`. Implement `process_unclassified_pdf(target_dir: Path, llm_client: LLMClient)`. It must scan for `.pdf`. If `_report.json` exists in the exact same directory alongside the PDF, log bypass and return. Otherwise, use `image_processing.py` to extract images, query LLM with `CategorizationResult` schema, and save intermediate `progress.json` and the final `[basename]_report.json` and `[basename]_categorized.pdf` using `src.utils.fs.atomic_write`.</action>
<read_first>
- src/categorization.py
- src/pdf/image_processing.py
- src/utils/fs.py
- ../file-categorizer/src/ai_classification.py
</read_first>
<acceptance_criteria>
- `process_unclassified_pdf` handles bypass logic correctly (CAT-02).
- Extracts images and queries LLM if not bypassed (CAT-01).
- Saves results as `progress.json`, `_report.json` and `_categorized.pdf` using atomic writes.
</acceptance_criteria>
</task>

### Wave 5: Main Orchestration

<task>
<description>Inject categorization into main pipeline</description>
<action>Modify `src/main.py` to call `process_unclassified_pdf(target_dir, llm_client)` BEFORE `validate_target_directory` is invoked.</action>
<read_first>
- src/main.py
- src/categorization.py
</read_first>
<acceptance_criteria>
- `process_unclassified_pdf` is called in `src/main.py` at the correct step.
- The pipeline executes end-to-end without crashing.
</acceptance_criteria>
</task>

## Artifacts this phase produces
- `src/core/categories.yaml` (new file copied from categorizer)
- `src/pdf/image_processing.py` (new module with functions: `extract_and_clean_page`, `adjust_levels`, `auto_deskew`, `process_pdf`)
- `CategorizationResult` (new Pydantic schema in `src/core/schemas.py`)
- `src/categorization.py` (new module with function: `process_unclassified_pdf`)

## Verification Criteria
- [ ] End-to-end run processes a raw PDF, invokes LLM, and creates `_report.json` and `_categorized.pdf`.
- [ ] Subsequent run bypasses processing because `_report.json` exists.

## must_haves
- D-01: Place the new logic in `src/categorization.py` — Runs before `cleaning.py`, keeps `main.py` lean and preserves functional pipeline.
- D-02: Adapt to use existing `LLMClient` wrapper — Maintains consistency, retry logic, and JSON schema enforcement instead of keeping standalone API calls.
- D-03: Exact port of `image_processing.py` without stripping OpenCV logic. Port `image_processing.py` and `ai_classification.py` exactly as they are without text-based OCR fallbacks.
- D-04: Bypass logic to prevent redundant LLM calls. Look for existing `_report.json` co-located with the PDF (in the exact same directory) to bypass extraction.
