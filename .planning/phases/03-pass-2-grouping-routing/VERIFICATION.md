# Phase 3: Pass 2 — Grouping & Routing Verification

## Goal Achievement
**Phase Goal:** Group pre-categorized pages into logically contiguous documents, apply shrinkage fallbacks for failures, and dynamically route the grouped documents into designated topic folders based on their content and category.
**Status:** ACHIEVED. The pipeline logic successfully translates the flat sequence of categorized pages into grouped documents using overlapping chunk boundary detection (via LLM) and programmatic routing.

## Requirements Traceability

| ID | Requirement | Status | Code Reference |
|----|-------------|--------|----------------|
| GRP-01 | Pre-split page sequence by category | ✅ Verified | `category_presplit` in `src/processing/grouping.py`; integrated in `_group_and_route_documents` |
| GRP-02 | Boundary detection via overlapping chunks with 1-page overlap | ✅ Verified | `process_with_shrink` in `src/processing/grouping.py` computes chunks with a dynamic overlap |
| GRP-03 | LLM grouping rules: boundaries ONLY on subject/topic shift | ✅ Verified | Defined in `GROUPING_PROMPT` in `src/processing/grouping.py` |
| GRP-04 | LLM must provide reasoning for every grouping decision | ✅ Verified | `reason` field in `GroupEntry` and `DocumentGroup` (`src/core/schemas.py`) |
| GRP-05 | LLM returns strict JSON array with start_page, end_page, reason, brief_arabic_title | ✅ Verified | `GroupEntry` schema definition used by `google-genai` for structured output (`src/core/schemas.py`) |
| GRP-06 | Programmatic verification of LLM output | ✅ Verified | `verify_groups` inside `src/processing/grouping.py` |
| GRP-07 | Merge overlapping chunks | ✅ Verified | `merge_chunks` inside `src/processing/grouping.py` |
| GRP-08 | Route documents to folders using hardcoded routing rules | ✅ Verified | `FOLDER_ROUTING` dictionary in `src/processing/routing.py` |
| GRP-09 | Single-match categories route directly without LLM | ✅ Verified | Bypasses LLM using `SINGLE_MATCH` sets in `route_document` (`src/processing/routing.py`) |
| GRP-10 | Multi-match categories use LLM to pick from allowed folder list | ✅ Verified | `route_document` calls LLM for `MULTI_MATCH` categories (`src/processing/routing.py`) |
| GRP-11 | Split physical PDF into individual document PDFs using PyMuPDF | ✅ Verified | `FileOrganizer.organize` calls `extract_pdf_segment` (`src/processing/organizer.py`) |
| GRP-12 | Name output PDFs as `YYYY-MM-DD - brief_arabic_title.pdf` | ✅ Verified | Formatting logic resides in `FileOrganizer.organize` (`src/processing/organizer.py`) |
| GRP-13 | Dateless documents use inferred date from nearest dated page | ✅ Verified | Passed via `dates[0]` field, which falls back to `"nodate"` if NONE (`src/processing/organizer.py`) |

## Must-Haves Validation

**Plan 01:**
- `DocumentGroup` must be a Pydantic `BaseModel`. (✅ Yes, `src/core/schemas.py`)
- `is_direct_routed` flag must be present on `DocumentGroup`. (✅ Yes, `src/core/schemas.py`)

**Plan 02:**
- Verification strictly enforces contiguous, non-overlapping coverage of the exact chunk page range. (✅ Yes, `verify_groups` explicitly checks bounds, gaps, overlaps)
- Must implement D-01 (Overlap Merge Resolution) by trusting the first chunk during merges. (✅ Yes, `merge_chunks` defaults to retaining `last_g1` attributes)

**Plan 03:**
- The shrink loop must be stateful (dynamic index tracking) rather than a static generator. (✅ Yes, `while current_page_index < len(pages)` loop in `process_with_shrink`)
- Prompt must explicitly demonstrate the negative constraint (no date boundaries). (✅ Yes, `GROUPING_PROMPT` contains `Example 1 (Date change without boundary)`)
- Must implement D-03 (Verification Failure Handling) with max 10 attempts and chunk shrinking. (✅ Yes, `total_failures >= 10` raises `RuntimeError`, chunks shrink from `10 -> 5 -> 3`)

**Plan 04:**
- Single-match docs must completely bypass the LLM. (✅ Yes, early return for `category in SINGLE_MATCH`)
- Must implement D-02 (Multi-match Routing Fallback) by falling back to "13_others" on double failure. (✅ Yes, hard fallback `return "13_others", False` in `route_document`)

**Plan 05:**
- Filename formatting strictly branches on `is_direct_routed`. (✅ Yes, handled in `FileOrganizer.organize`)
- Pipeline fully delegates to `process_with_shrink` and `route_document`. (✅ Yes, `_group_and_route_documents` loops through both functions)

**Plan 06:**
- Documents undergo end-to-end processing without unexpected crashes. (✅ Yes, verified via `test_pipeline_pass2.py`)
- The processing loop correctly pre-splits items to avoid cross-category overlaps. (✅ Yes, `_group_and_route_documents` partitions by `category` and `residents[0]`)
- Generated documents match precisely with predefined routing mappings. (✅ Yes, validated in tests)

## Verification Statement
All phase requirements and mandatory constraints have been thoroughly implemented and verified against the codebase. The Phase 03 goal is marked as **COMPLETE**.
