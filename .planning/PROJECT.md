# Arabic Housing Document Categorizer

## What This Is

An automated document processing application that takes scanned Arabic housing files (often up to 200 pages long), extracts their text via multimodal vision, and processes them using the Gemma 4 31b model. It organizes the disorganized input into a deeply structured directory hierarchy, categorizing pages into smaller PDF files by house number, chronological residents, and 13 specific document types, while intelligently keeping multi-page letters intact.

## Core Value

Accurately parsing, splitting, and categorizing large, disorganized scanned Arabic documents into an exact 13-category chronological folder structure without losing the context of multi-page topics.

## Requirements

### Validated

- ✓ Implement robust Arabic OCR pipeline for scanned PDFs and images (replaced by direct LLM vision) — Phase 01
- ✓ Integrate with the Gemma 4 31b model via the user's specific API/hosting setup for document understanding — Phase 01
- ✓ Detect page continuations so multi-page letters on the same topic stay in a single combined PDF — Phase 01
- ✓ Implement PDF splitting logic to extract specific pages into smaller PDF files — Phase 01

### Active

- ✓ Extract the House Number to create the root directory (e.g., `683`) — v1.0
- ✓ Extract Resident information, double-sort them, and organize chronologically — v1.0
- ✓ Handle structural edge cases: "Amar Takhsees" and generic house-related letters — v1.0
- ✓ Generate 13 distinct subfolders per person — v1.0
- ✓ Build a desktop GUI to wrap the CLI logic — v1.0

### Active

*(None — planning next milestone)*

### Out of Scope

- [Saving text only] — We must split the original file into smaller PDF files to retain visual integrity, not just save text.
- [Using default large context models like Gemini 1.5 Pro natively] — User explicitly requested to route processing through Gemma 4 31b.

## Current State

Shipped **v1.0 MVP**. The core pipeline now correctly processes Arabic documents via Gemma 4 31b, resolves primary tenants across continuous pages, and generates the required chronological 13-category folder structure. A `Tkinter` desktop GUI was built to make it easy to select PDFs and output directories.

## Next Milestone Goals

- Collect user feedback from the v1.0 deployment.
- Address any edge cases in Arabic name normalization or OCR vision gaps.
- Consider moving towards v2.0 requirements (e.g., Web dashboard or DB tracking) if prioritized.

## Context

- The input housing documents are scanned Arabic files, highly disorganized, and can contain 200+ pages.
- Resident details are not always sorted chronologically in the input file; double sorting is required (first by who lived there and who didn't, then chronologically).
- Some letters relate to the house itself and not a specific person.
- The model must perform complex NLP categorization on OCR'd Arabic text to determine the specific document type out of the 13 categories.

## Constraints

- **Language and Formatting**: Arabic OCR — Scanned Arabic text can be difficult to extract accurately, which is a prerequisite for the LLM to categorize the pages.
- **Model Choice**: Gemma 4 31b — The application must use this specific model, relying on the user's API setup.
- **Document Integrity**: Page Continuation — Continuations of letters must be kept together in a single PDF file and not split arbitrarily page-by-page.
- **Output Format**: PDF Extraction — The final categorized files must be smaller PDFs sliced from the original PDF.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use Gemma 4 31b | User explicitly requested this specific model over alternatives | Verified in Phase 01 |
| Split PDFs | Extracting smaller PDFs retains the original visual integrity of the documents rather than just raw text | Verified in Phase 01 |
| Multimodal Vision over traditional OCR | Gemma-4-31b handles Arabic scans natively, skipping a fragile secondary OCR step | Verified in Phase 01 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-23 after v1.0 milestone*
