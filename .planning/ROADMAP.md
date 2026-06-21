# Roadmap

## Active Roadmap

**3 phases** | **15 requirements mapped** | All v1 requirements covered ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | OCR & PDF Pipeline | Build the ingestion, OCR extraction, and PDF manipulation logic | OCR-01, OCR-02, OCR-03 | 3 |
| 2 | LLM Integration | 2/3 | In Progress|  |
| 3 | Filesystem Generator | Orchestrate the entire flow into structured folders and save PDFs | SYS-01, SYS-02, SYS-03, SYS-04, SYS-05, SYS-06 | 3 |

### Phase Details

**Phase 1: OCR & PDF Pipeline**
**Goal:** Build the ingestion, OCR extraction, and PDF manipulation logic
**Requirements:** OCR-01, OCR-02, OCR-03
**Success criteria:**

1. Can load a multi-page scanned Arabic PDF.
2. Extracts Arabic text from every page successfully using an OCR engine.
3. Can split an original PDF into a separate PDF file for a specific page range without quality loss.

**Phase 2: LLM Integration**
**Goal:** Interface with Gemma 4 31b to analyze text and classify pages
**Requirements:** LLM-01, LLM-02, LLM-03, LLM-04, LLM-05
**Success criteria:**

1. Successfully sends a prompt with extracted Arabic text to the Gemma 4 31b API endpoint.
2. Returns a structured JSON response identifying house, person, category, and continuation flag.
3. Accurately determines if page N+1 is a continuation of page N's topic.

**Phase 3: Filesystem Generator**
**Goal:** Orchestrate the entire flow into structured folders and save PDFs
**Requirements:** SYS-01, SYS-02, SYS-03, SYS-04, SYS-05, SYS-06
**Success criteria:**

1. Creates the correct double-sorted folder hierarchy (House -> Person -> 13 Categories).
2. "Amar Takhsees" and house-generic letters are successfully routed to root-level subfolders.
3. Combines continuous pages and saves them as a single sliced PDF in the correct category folder.
