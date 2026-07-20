# Phase 21: System Unification - Research

## 1. Technical Approach

### 1.1 Architecture & Module Placement (D-01)
Create a new module `src/categorization/categorization.py` to handle the "Pass 0" step of the pipeline.
In `src/main.py`, inject the categorization logic *before* `validate_target_directory` is called. 
- The pipeline will look for `.pdf` files in the `target_dir`.
- It will execute the categorization pass on raw PDFs.
- Once completed (or bypassed), `validate_target_directory` can pick up the `_categorized.pdf` and `_report.json` exactly as it did before.

### 1.2 Bypass Logic (CAT-02 & D-04)
Within `src/categorization/categorization.py` (`process_unclassified_pdf`):
- Scan the target directory for `_report.json`.
- If `_report.json` exists in the exact same directory alongside the PDF, log a bypass message and immediately skip the image extraction and LLM classification process.
- If it doesn't exist, proceed to rename the raw `.pdf` (if necessary) to `[basename]_categorized.pdf` and execute the extraction to generate `[basename]_report.json`.

### 1.3 Image Processing Pipeline (D-03)
- Create `src/pdf/image_processing.py`.
- Port `extract_and_clean_page`, `adjust_levels`, `auto_deskew`, and `process_pdf` exactly as they are from `file-categorizer/src/image_processing.py`.
- This ensures the highly tuned OpenCV cleaning pipeline (auto-deskew, illumination normalization, diacritic boosting) is preserved verbatim.

### 1.4 LLM Client Integration & Pydantic Schemas (D-02)
- Instead of using the raw `google-genai` SDK and string-based manual JSON parsing from `file-categorizer/src/ai_classification.py`, we will use `src.llm.llm.LLMClient`.
- We will define Pydantic models in `src/core/schemas.py` that map to the extraction targets defined in `categories.yaml`.
- By passing `response_schema=MyPydanticModel` to `llm_client.generate_content(...)`, we get automatic JSON schema enforcement, model fallback, and retry resilience built into the existing architecture.

## 2. Existing Patterns to Leverage
- **Resilient LLM Routing**: Using `LLMClient.generate_content()` ensures rate limits (429s) and server errors (503s) are handled natively without re-implementing sleep loops.
- **Atomic File System Writes**: Use `src.utils.fs.atomic_write` for saving the intermediate `progress.json` and final `_report.json` to prevent file corruption during unexpected crashes.
- **Pydantic Validation**: `src/core/schemas.py` is the established pattern for enforcing LLM structure. The prompt instructions from `categories.yaml` will be mapped directly to Pydantic `Field(description=...)` attributes.

## 3. Dependencies
To port `image_processing.py` successfully, the following packages from the `file-categorizer` environment must be appended to `file-organizer/requirements.txt`:
- `opencv-python`
- `numpy`
*(Note: `PyMuPDF` / `fitz` is already present).*

Additionally, the `categories.yaml` file from the root of `file-categorizer` must be copied into the `file-organizer` codebase (e.g., to `src/core/categories.yaml` or the root directory) so the categorization logic has access to the classification rules.

## 4. Unknowns/Risks
- **Image Payload Limits**: `file-categorizer` explicitly used the Google GenAI File API (`client.files.upload`) to upload images. If we switch to passing images inline via the `contents` array through `LLMClient`, we must ensure the base64/inline payload does not exceed Google's inline limits. Alternatively, we might need to expose an `.upload_file()` method on the `LLMProvider` protocol to replicate the exact upload/delete behavior.
- **Schema Dynamism vs Static Typing**: `categories.yaml` defines varying extraction rules per category. Since Pydantic expects compile-time types, we will need to define a static Union of schemas in `src/core/schemas.py` that covers all possible extractions (e.g., `sender`, `receiver`, `image_contents`), or generate schemas dynamically using `pydantic.create_model()`.
- **Directory Name Constraints**: `main.py` currently expects the `target_dir` to be named after the `house_id` or parses it from the file names. The Categorization pass must gracefully extract the basename of the raw PDF to generate the `<basename>_categorized.pdf` without breaking downstream expectations.
