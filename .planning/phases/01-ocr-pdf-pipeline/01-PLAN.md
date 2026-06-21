# Phase 1: OCR & PDF Pipeline

**Phase**: 1
**Domain**: Document Ingestion, Image Extraction, and PDF Splitting

## Goal
Build the ingestion, OCR extraction, and PDF manipulation logic using PyMuPDF and the Gemma multimodal endpoint.

## Architecture & Implementation Steps

### 1. Project Initialization
- Create `src/` directory.
- Initialize `requirements.txt` with `PyMuPDF`, `tenacity`, `httpx` (or `google-generativeai`).
- Create `main.py` entrypoint.

### 2. Ingestion Module (`src/ingest.py`)
- Implement `PdfIngestor` class.
- Add method `extract_pages_as_images(pdf_path: str)`:
  - Open PDF with `fitz.open()`.
  - Yield a tuple `(page_index, image_bytes)` for each page using `page.get_pixmap(dpi=150)`.

### 3. LLM/OCR Module (`src/llm.py`)
- Implement `GemmaClient` class.
- Add async/threaded method `process_image(image_bytes)`:
  - Formulate the multimodal prompt asking for House Number, Resident Name, Category (out of the 13 defined), and a `is_continuation` boolean.
  - Implement retry logic using `@tenacity.retry` for handling `429 Too Many Requests`.

### 4. Orchestration & Concurrency (`src/pipeline.py`)
- Implement `Pipeline` class.
- Use `concurrent.futures.ThreadPoolExecutor(max_workers=5)`.
- Submit each page's `image_bytes` to the `GemmaClient`.
- Gather results and re-order them sequentially based on `page_index`.
- Handle the `is_continuation` logic to merge continuous pages logically into groups.

### 5. PDF Splitting (`src/split.py`)
- Implement `extract_pdf_segment(source_pdf, start_page, end_page, output_path)` using PyMuPDF to extract and save the required pages as smaller PDFs.

## Verification
- Run tests verifying image extraction and mock the Gemma API to test parallel processing limits.
