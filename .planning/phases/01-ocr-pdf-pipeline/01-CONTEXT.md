# Phase 1 Context

**Phase**: 1
**Domain**: Document Ingestion, Image Extraction, and PDF Splitting (Pre-LLM processing pipeline)

## Decisions Captured

### OCR Engine vs Multimodal LLM
- **Decision**: Bypass traditional OCR (like Tesseract or Google Cloud Vision) entirely. The pipeline will render PDF pages into images and pass the images directly to the Gemma 4 31b multimodal endpoint for text extraction and analysis.
- **Rationale**: User preference; modern multimodal models often outperform traditional OCR engines on messy/complex scans.

### PDF Manipulation Tooling
- **Decision**: Use `PyMuPDF` (fitz) for handling PDF files.
- **Rationale**: PyMuPDF is extremely fast, robust, and excels at both rendering pages to high-quality images (for Gemma) and safely splitting/extracting pages into new PDFs.

### Concurrency
- **Decision**: Use parallel processing (e.g., multithreading or `asyncio`) when processing the 200+ page documents.
- **Rationale**: Drastically reduces processing time for large documents. Memory usage will need to be bounded with concurrency limits/semaphores.

## Code Context

*(No prior code context yet — Greenfield phase)*

## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
