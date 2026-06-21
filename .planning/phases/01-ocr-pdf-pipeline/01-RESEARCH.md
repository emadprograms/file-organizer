# Phase 1 Research

**Phase**: 1
**Domain**: Document Ingestion, Image Extraction, and PDF Splitting

## Technical Strategy
The goal is to load large (200+ page) Arabic PDFs, render them to images, and use the Gemma 4 31b multimodal model to perform OCR and categorization simultaneously. PyMuPDF will handle the document manipulation, and we will use parallel processing for speed.

## Findings & Best Practices

1. **PyMuPDF Rendering**: 
   - Opening documents: `doc = fitz.open(pdf_path)`
   - Rendering pages: `pix = page.get_pixmap(dpi=150)` (Use an optimal DPI to balance image size and text legibility).
   - Exporting to bytes: `image_bytes = pix.tobytes("png")`. This is necessary for API transmission.

2. **Parallel Processing & Resource Limits**:
   - Holding 200 hi-res images in memory will cause OOM crashes.
   - We must stream the PDF processing or use a bounded concurrency model (e.g., `concurrent.futures.ThreadPoolExecutor(max_workers=5)`).

3. **API Rate Limiting**:
   - Gemma API requests running in parallel are highly susceptible to HTTP 429 Rate Limit errors.
   - Implementation MUST include an exponential backoff retry mechanism (e.g., using the `tenacity` Python package).

4. **Context and Continuity**:
   - Since pages are processed in parallel, the model won't inherently know if Page 5 is a continuation of Page 4.
   - The LLM prompt must return a "continuation" boolean, and the post-processing step (which runs sequentially after parallel extraction) will merge pages logically.

## Required Dependencies
- `PyMuPDF`: For PDF splitting and image rendering.
- `tenacity`: For API retry logic.
- HTTP client library (e.g., `httpx` or `google-generativeai`) depending on the exact Gemma API endpoint.

## Architecture Recommendations for the Planner
- **Ingestion Module**: A generator that yields `(page_number, image_bytes)` using PyMuPDF.
- **LLM Module**: Async/Threaded worker that posts the image to Gemma and returns a structured JSON response.
- **Orchestration Module**: Manages the bounded thread pool, aggregates the JSON results, and reconstructs the page continuity.
