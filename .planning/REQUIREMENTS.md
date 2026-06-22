# Requirements

## v1 Requirements

### PDF Processing & OCR
- [ ] **OCR-01**: System can ingest a multi-page scanned PDF file.
- [ ] **OCR-02**: System applies Arabic OCR to extract text from each page.
- [ ] **OCR-03**: System can split a large PDF into smaller multi-page or single-page PDFs without losing visual quality.

### LLM Analysis
- [ ] **LLM-01**: System sends extracted Arabic text to the Gemma 4 31b endpoint.
- [ ] **LLM-02**: LLM identifies the House Number from the document text.
- [ ] **LLM-03**: LLM extracts the name of the resident the document pertains to.
- [ ] **LLM-04**: LLM categorizes the document into one of the 13 defined categories (or "Amar Takhsees" / House generic).
- [ ] **LLM-05**: LLM determines if a page is a continuation of the previous page's letter/topic.

### Filesystem Organization
- [ ] **SYS-01**: System creates a root folder named after the House Number (e.g., `683`).
- [ ] **SYS-02**: System creates a chronological numbered folder for each resident (e.g., `1_Mohammad`, `2_Ahmed`).
- [ ] **SYS-03**: System creates special folders at the root for "Amar Takhsees" (didn't live there) and house-specific details.
- [ ] **SYS-04**: System generates exactly 13 specific subfolders inside each resident's folder.
- [ ] **SYS-05**: System saves the sliced PDF documents into their corresponding category folders.
- [ ] **SYS-06**: Pages identified as continuations are merged into a single PDF file rather than saved separately.

### GUI Application
- [ ] **GUI-01**: Provide a local GUI application (Tkinter) to allow the user to select the input PDF and output directory.
- [ ] **GUI-02**: Display a progress bar or text log to show current processing state (e.g., which pages are being processed, which files are being generated).

## v2 Requirements (Deferred)
- [ ] **UI-01**: Web dashboard for uploading files instead of CLI.
- [ ] **DB-01**: Database tracking of processed documents and extracted metadata.

## Out of Scope
- **Pure Text Output**: The user specifically requested extracting the original pages as smaller PDFs, not just saving the raw extracted text.
- **Other LLMs natively**: The solution must use Gemma 4 31b per user constraint, not default to Gemini 1.5 Pro natively.

## Traceability

*(To be filled by roadmap)*
