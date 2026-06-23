# Roadmap

## Active Roadmap

**2 phases** | **17 requirements mapped** | All v1 requirements covered ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Data Pipeline & LLM Integration | 6/8 | Complete    | 2026-06-22 |
| 2 | Filesystem Generator & GUI | 2/2 | Complete   | 2026-06-22 |

### Phase Details

### Phase 1: Data Pipeline & LLM Integration

**Goal:** Build the ingestion, OCR extraction, interface with Gemma 4 31b to analyze text, and group tenants logically.
**Requirements:** OCR-01, OCR-02, OCR-03, LLM-01, LLM-02, LLM-03, LLM-04, LLM-05
**Success criteria:**

1. Can load a multi-page scanned Arabic PDF and extract text.
2. Returns a structured JSON response identifying house, person, category, and maps families correctly.
3. Groups documents logically, correctly preserving timeline and merging wives/children into the head of household.

### Phase 2: Filesystem Generator & GUI

**Goal:** Orchestrate the entire flow into structured folders, save PDFs, and build a Tkinter GUI to wrap the CLI.
**Requirements:** SYS-01, SYS-02, SYS-03, SYS-04, SYS-05, SYS-06, GUI-01, GUI-02
**Success criteria:**

1. Creates the correct double-sorted folder hierarchy (House -> Person -> 13 Categories).
2. "Amar Takhsees" and house-generic letters are successfully routed to root-level subfolders.
3. Combines continuous pages and saves them as a single sliced PDF in the correct category folder.
4. Application launches a window with input for selecting the PDF file and output folder.
5. Contains a "Run" button to execute the pipeline.
6. Displays console output or a progress bar reflecting execution state.
