# Phase 21: System Unification - Patterns

This document maps the architectural elements and technical requirements gathered from `CONTEXT.md` and `RESEARCH.md` into concrete file operations.

## 1. `src/categorization/categorization.py` (New File)
- **Role**: Handles the "Pass 0" step of the pipeline. It bypasses already processed PDFs, or runs the image extraction and AI classification pass to produce a `[basename]_categorized.pdf` and `[basename]_report.json`.
- **Data Flow**: Receives `target_dir` from `main.py`. Scans for `.pdf`. If `_report.json` exists in the exact same directory alongside the PDF, bypasses processing. Otherwise, extracts images using `src/pdf/image_processing.py`, reads `categories.yaml`, builds LLM queries via `src/llm/llm.py` using Pydantic schemas, and saves the output.
- **Closest Existing Analog**: The orchestration functions in `src/main.py` (e.g., `run_cleaning_pass`) and the pipeline logic in `src/pipeline/pipeline.py` (e.g., `_clean_documents`).
- **Concrete Code Excerpt** (Conceptual mapping from `file-categorizer`):
  ```python
  def process_unclassified_pdf(target_dir: Path, llm_client: LLMClient) -> None:
      # Bypass Logic (CAT-02 & D-04)
      json_files = list(target_dir.glob("*_report.json"))
      pdf_files = list(target_dir.glob("*.pdf"))
      if json_files:
          logger.info(f"Bypassing categorization, found {json_files[0]}")
          return
      # Proceed with renaming to _categorized.pdf and extraction...
  ```

## 2. `src/main.py` (Modified File)
- **Role**: Pipeline orchestrator and entry point.
- **Data Flow**: Needs to invoke `src/categorization/categorization.py` before `validate_target_directory` is called to ensure raw PDFs are transformed into the expected `_categorized.pdf` and `_report.json` state.
- **Closest Existing Analog**: Existing orchestration logic for `run_cleaning_pass` and `run_grouping_pass`.
- **Concrete Code Excerpt** (Where injection occurs):
  ```python
  # Before this existing block:
  # house_id = validate_target_directory(target_dir)
  
  # Inject categorization logic:
  from src.categorization import process_unclassified_pdf
  process_unclassified_pdf(target_dir, llm_client)
  
  # Then proceed:
  house_id = validate_target_directory(target_dir)
  ```

## 3. `src/pdf/image_processing.py` (New File)
- **Role**: OpenCV-based image extraction and cleaning pipeline (auto-deskew, illumination normalization, diacritic boosting).
- **Data Flow**: Reads a `fitz.Document`, processes it page by page, and saves high-quality cleaned `.png` images to a temporary directory tracked by `progress.json`.
- **Closest Existing Analog**: Direct port from `../file-categorizer/src/image_processing.py`.
- **Concrete Code Excerpt** (From `file-categorizer/src/image_processing.py`):
  ```python
  def extract_and_clean_page(pdf_document: fitz.Document, page_num: int, tmp_dir: str) -> str:
      page = pdf_document.load_page(page_num)
      pix = page.get_pixmap(dpi=300)
      # ... OpenCV processing (extract Green Channel, Auto-Deskew, Illumination Normalization, Diacritic Boost) ...
      cv2.imwrite(clean_path, sharpened)
      return clean_path
  ```

## 4. `src/core/schemas.py` (Modified File)
- **Role**: Pydantic definitions for enforcing structured JSON extraction from the LLM.
- **Data Flow**: Passed as the `response_schema` argument to `LLMClient.generate_content`. Maps the extraction rules defined in `categories.yaml` to strict typing.
- **Closest Existing Analog**: `PageData` and `DocumentGroup` schemas in the same file.
- **Concrete Code Excerpt** (Pattern to implement):
  ```python
  from pydantic import BaseModel, Field

  class CategorizationResult(BaseModel):
      category: str = Field(description="The categorized document type.")
      # Extra dynamic fields will be evaluated via Unions or create_model()
  ```

## 5. `src/llm/llm.py` and `src/llm/providers.py` (Modified Files)
- **Role**: The core LLM orchestration logic.
- **Data Flow**: Needs to support inline image passing or expose a `.upload_file()` method (as noted in Unknowns/Risks) to replace the standalone `google-genai` SDK usage from the original `ai_classification.py`.
- **Closest Existing Analog**: `GeminiProvider.generate()` which currently handles `contents: list[dict[str, Any]]`.
- **Concrete Code Excerpt**:
  ```python
  # Pattern to handle images in GeminiProvider.generate:
  response = self.client.models.generate_content(
      model=actual_model,
      contents=[image_file, prompt], # Handling multi-modal input
      config=types.GenerateContentConfig(**kwargs)
  )
  ```

## 6. `requirements.txt` (Modified File)
- **Role**: Project dependencies list.
- **Data Flow**: Standard `pip` installation target.
- **Concrete Code Excerpt**:
  ```text
  opencv-python
  numpy
  ```

## 7. `src/core/categories.yaml` (New File)
- **Role**: Contains the categorization rules and extraction instructions mapping.
- **Data Flow**: Read directly by `src/categorization/categorization.py`.
- **Closest Existing Analog**: `../file-categorizer/categories.yaml`.
