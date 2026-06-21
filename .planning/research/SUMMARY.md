# Project Research Summary

## Key Findings

**Stack:** 
- Python as the primary orchestration language.
- `PyMuPDF` (fitz) or `PyPDF2` for robust PDF page extraction and splitting.
- `pdf2image` + `Tesseract OCR` (with `ara` language data) or Google Cloud Vision API for extracting Arabic text from scanned images.
- `google-generativeai` (Gemini API SDK) or custom HTTP client to interface with the Gemma 4 31b endpoint.

**Table Stakes:** 
- Robust Arabic OCR capable of handling noisy scans.
- PDF manipulation to extract specific page ranges into new PDF files.
- Double-sorting logic (House -> People -> Categories).

**Watch Out For:** 
- **Context Window Limits**: A 200-page OCR'd document might overwhelm Gemma 31b's context window. Processing the document in chunks (e.g., 10-20 pages at a time) is necessary.
- **Continuations**: Letters spanning multiple pages must not be split. The LLM prompt must explicitly ask "Is this page a continuation of the previous letter?".
- **Hallucinations in OCR**: Bad scans produce garbage text. The LLM prompt must be resilient to OCR errors.

## Implications for Roadmap

- **Phase 1** must establish the OCR and PDF splitting pipeline before introducing the LLM.
- **Phase 2** should implement the LLM integration and the specific 13-category prompt logic.
- **Phase 3** should handle the filesystem generation and final PDF routing.
