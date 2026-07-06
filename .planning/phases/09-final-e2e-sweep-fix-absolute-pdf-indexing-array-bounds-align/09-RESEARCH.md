# Phase 09: final-e2e-sweep-fix-absolute-pdf-indexing-array-bounds-align - Research

## Overview
This phase delivers critical bug fixes for end-to-end processing, focusing on PDF indexing alignment (0-based vs 1-based), array bounds, date resolution consistency, logging transparency for LLMs, and pipeline structural integrity.

## Architecture and Scope

### PDF Page Indexing Strategy
- Standardize on 0-based indexing internally. Convert input to 0-based immediately, work in 0-based throughout the pipeline, and convert to 1-based only for output. (D-01)
- Implement strict array bounds validation. Abort processing if a referenced page is out of bounds to prevent silent data loss or mangled outputs. (D-02)
- Fail reconciliation completely if any page is dropped. Require the pipeline to account for every single page from input to output, otherwise fail the entire house processing. (D-03)
- Centralize the logic for index bounds resolution and 0-based conversion in a utility module for consistency everywhere. (D-04)

### LLM Logging Format
- Write detailed LLM request/responses to separate JSON files inside a `logs/traces/` directory, keeping the main log readable. (D-05)
- Explicitly parse the token usage metadata and print it at INFO level in the main log to track costs and limits. (D-06)
- Log errors to trace files and warn in the console. Save the exact malformed output in a `.error.json` trace file. (D-07)

### Pipeline Architecture Refactoring
- Apply targeted, precise fixes to the exact locations where array bounds fail and indexing is mismatched, minimizing regression risk. (D-08)
- Ensure all dates are fully resolved to absolute values in Pass 1, so Pass 2 and Routing never have to guess or recalculate. (D-09)
- Use safe defaults for bounds/index errors at runtime. If an indexing bug occurs in production, gracefully dump the affected pages to the "Unassigned" folder rather than crashing the whole pipeline. (D-10)

## Implementation Details

### Centralized Utility Module for Indexing
- Create or update a utility module to handle bounds resolution and 0-based conversions securely.
- Include methods to check bounds given a max length, convert from 1-based to 0-based, and vice versa.

### Logging Subsystem Enhancements
- Update logging architecture to support writing to `logs/traces/`.
- Handle token usage parsing from the LLM model response payload.
- Update `LLMClient` to write specific trace JSON files on normal requests and `.error.json` traces on exceptions or bad schema responses.

### Pipeline Changes
- **Pass 1 Date Resolution:** Ensure the date resolution step guarantees all pages receive a fully resolved date (no nulls passing into Pass 2 logic without proper defaults or resolution). 
- **Array Bounds Validation:** Introduce robust checks before any sequence slicing or indexing in PyMuPDF logic and LLM chunking algorithms.
- **Reconciliation Failure:** Make the final page count check abort or log explicitly a FATAL failure if the final output page count does not perfectly match the original input.
- **Runtime Safe Defaults:** Add a catch-all in routing and output PDF generation that captures out-of-bounds or failed indices, gracefully routing those pages into the `Unassigned` folder instead of crashing the process.

## Validation Architecture
- **E2E Integration Testing:** Run the pipeline with a fixture that has out-of-bounds indexing in the JSON payload, verifying that it routes these edge cases to the "Unassigned" directory gracefully without crashing.
- **Unit Testing (Indexing Utility):** Test the boundary checking and 1-based to 0-based conversion utility. Pass normal ranges, out-of-bounds ranges, edge indices, and verify exceptions or correct mapping.
- **Unit Testing (LLM Logs):** Mock `LLMClient` responses, including token metadata, and assert that the correct trace files (`logs/traces/*.json` and `logs/traces/*.error.json`) are written and token usage is logged at INFO level.
- **Reconciliation Tests:** Trigger a missing page deliberately and assert that the reconciliation step fails the whole house processing with the expected error output.
- **Pass 1 Date Validation:** Ensure tests assert that Pass 2 inputs NEVER contain unresolved relative or null dates.

## Open Questions / Follow-ups
- None identified; the context explicitly defined exact behaviors needed for this sweep.
