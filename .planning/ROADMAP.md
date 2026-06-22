# Roadmap

## Active Roadmap

**2 phases** | **15 requirements mapped** | All v1 requirements covered ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Data Pipeline & LLM Integration | 6/8 | Complete    | 2026-06-22 |
| 2 | Filesystem Generator | Orchestrate the entire flow into structured folders and save PDFs | SYS-01, SYS-02, SYS-03, SYS-04, SYS-05, SYS-06 | 3 |

### Phase Details

**Phase 1: Data Pipeline & LLM Integration**
**Goal:** Build the ingestion, OCR extraction, interface with Gemma 4 31b to analyze text, and group tenants logically.
**Requirements:** OCR-01, OCR-02, OCR-03, LLM-01, LLM-02, LLM-03, LLM-04, LLM-05
**Success criteria:**

1. Can load a multi-page scanned Arabic PDF and extract text.
2. Returns a structured JSON response identifying house, person, category, and maps families correctly.
3. Groups documents logically, correctly preserving timeline and merging wives/children into the head of household.

**Phase 2: Filesystem Generator**
**Goal:** Orchestrate the entire flow into structured folders and save PDFs
**Requirements:** SYS-01, SYS-02, SYS-03, SYS-04, SYS-05, SYS-06
**Success criteria:**

1. Creates the correct double-sorted folder hierarchy (House -> Person -> 13 Categories).
2. "Amar Takhsees" and house-generic letters are successfully routed to root-level subfolders.
3. Combines continuous pages and saves them as a single sliced PDF in the correct category folder.
